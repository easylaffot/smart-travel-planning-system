"""Sequential CrewAI assembly for the travel-planning specialists."""

from typing import Any

from crewai import Agent, Crew, Process, Task

from smart_travel_planner.agents import TravelAgentFactory
from smart_travel_planner.config.settings import Settings, get_settings
from smart_travel_planner.crew.task_factory import TravelTaskFactory
from smart_travel_planner.utils.exceptions import CrewConfigurationError


class TravelCrewFactory:
    """Assemble agents and tasks without executing the crew."""

    def __init__(
        self,
        *,
        llm: Any | None = None,
        settings: Settings | None = None,
        agent_factory: TravelAgentFactory | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.agent_factory = agent_factory or TravelAgentFactory(
            llm=llm,
            settings=self.settings,
        )

        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}

    def build(self) -> Crew:
        """Construct the sequential crew without calling kickoff."""

        self.agents = self.agent_factory.build()

        task_factory = TravelTaskFactory(self.agents)
        self.tasks = task_factory.build()

        ordered_agents = [
            self.agents[TravelAgentFactory.COORDINATOR],
            self.agents[TravelAgentFactory.DESTINATION_RESEARCHER],
            self.agents[TravelAgentFactory.HOTEL_TRANSPORT_SPECIALIST],
            self.agents[TravelAgentFactory.BUDGET_ANALYST],
            self.agents[TravelAgentFactory.ITINERARY_PLANNER],
        ]

        ordered_tasks = task_factory.ordered_tasks(self.tasks)

        crew_kwargs: dict[str, Any] = {
            "agents": ordered_agents,
            "tasks": ordered_tasks,
            "process": Process.sequential,
            "verbose": self.settings.crew_verbose,
            "memory": False,
            "cache": self.settings.crew_cache_enabled,
        }

        if self.settings.crew_max_rpm is not None:
            crew_kwargs["max_rpm"] = self.settings.crew_max_rpm

        try:
            crew = Crew(**crew_kwargs)
        except (TypeError, ValueError) as exc:
            raise CrewConfigurationError(
                "CrewAI could not assemble the sequential travel crew."
            ) from exc

        self._validate_crew(crew)
        return crew

    def _validate_crew(self, crew: Crew) -> None:
        """Validate the assembled crew before any execution."""

        if len(self.agents) != 5:
            raise CrewConfigurationError("The travel crew must contain exactly five agents.")

        if len(self.tasks) != 6:
            raise CrewConfigurationError("The travel crew must contain exactly six tasks.")

        if crew.process != Process.sequential:
            raise CrewConfigurationError("The initial travel crew must use sequential execution.")
