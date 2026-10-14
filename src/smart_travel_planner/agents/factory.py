"""Factory for the five specialized CrewAI travel agents."""

from collections.abc import Mapping
from typing import Any

from crewai import Agent
from crewai.tools import BaseTool

from smart_travel_planner.config.settings import Settings, get_settings
from smart_travel_planner.services import ensure_llm
from smart_travel_planner.tools import (
    BudgetCalculatorTool,
    DestinationSearchTool,
    HotelSearchTool,
    ItineraryScheduleValidatorTool,
    LocationTool,
    RoutingTool,
    TransportSearchTool,
    WeatherTool,
)
from smart_travel_planner.utils.exceptions import CrewConfigurationError


class TravelAgentFactory:
    """Create role-specific travel agents with restricted tools."""

    COORDINATOR = "travel_coordinator"
    DESTINATION_RESEARCHER = "destination_researcher"
    HOTEL_TRANSPORT_SPECIALIST = "hotel_transport_specialist"
    BUDGET_ANALYST = "budget_analyst"
    ITINERARY_PLANNER = "itinerary_planner"

    EXPECTED_AGENT_KEYS = {
        COORDINATOR,
        DESTINATION_RESEARCHER,
        HOTEL_TRANSPORT_SPECIALIST,
        BUDGET_ANALYST,
        ITINERARY_PLANNER,
    }

    def __init__(
        self,
        llm: Any | None = None,
        settings: Settings | None = None,
        tool_overrides: Mapping[str, list[BaseTool]] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm = ensure_llm(llm, settings=self.settings)
        self.tool_overrides = dict(tool_overrides or {})

    def build(self) -> dict[str, Agent]:
        """Build and validate all five agents."""

        agents = {
            self.COORDINATOR: self._build_coordinator(),
            self.DESTINATION_RESEARCHER: (self._build_destination_researcher()),
            self.HOTEL_TRANSPORT_SPECIALIST: (self._build_hotel_transport_specialist()),
            self.BUDGET_ANALYST: self._build_budget_analyst(),
            self.ITINERARY_PLANNER: self._build_itinerary_planner(),
        }

        self._validate_agents(agents)
        return agents

    def _agent(
        self,
        *,
        role: str,
        goal: str,
        backstory: str,
        tools: list[BaseTool],
    ) -> Agent:
        """Create one consistently configured CrewAI agent."""

        kwargs: dict[str, Any] = {
            "role": role,
            "goal": goal,
            "backstory": backstory,
            "llm": self.llm,
            "tools": tools,
            "verbose": self.settings.crew_verbose,
            "allow_delegation": False,
            "max_iter": self.settings.agent_max_iterations,
            "max_execution_time": (self.settings.agent_max_execution_seconds),
            "cache": self.settings.crew_cache_enabled,
        }

        if self.settings.crew_max_rpm is not None:
            kwargs["max_rpm"] = self.settings.crew_max_rpm

        return Agent(**kwargs)

    def _tools(
        self,
        agent_key: str,
        defaults: list[BaseTool],
    ) -> list[BaseTool]:
        """Return injected tools when supplied, otherwise defaults."""

        override = self.tool_overrides.get(agent_key)

        if override is not None:
            return list(override)

        return defaults

    def _build_coordinator(self) -> Agent:
        return self._agent(
            role="Travel Coordinator",
            goal=(
                "Interpret customer travel requirements, coordinate the "
                "specialists, preserve constraints, and validate that the "
                "final plan is complete, sourced, and financially accurate."
            ),
            backstory=(
                "You are a senior travel operations coordinator experienced "
                "in converting customer requirements into controlled work "
                "plans. You do not invent prices or research. You review "
                "specialist outputs, preserve customer constraints, and "
                "clearly identify unresolved risks."
            ),
            tools=self._tools(self.COORDINATOR, []),
        )

    def _build_destination_researcher(self) -> Agent:
        return self._agent(
            role="Destination Research Specialist",
            goal=(
                "Research attractions, local experiences, weather, location "
                "details, and practical routing information that match the "
                "customer's destination and interests."
            ),
            backstory=(
                "You are a destination research professional who relies on "
                "assigned tools for current information. You preserve source "
                "URLs and data-mode labels, distinguish mock information from "
                "live research, and never invent unavailable weather."
            ),
            tools=self._tools(
                self.DESTINATION_RESEARCHER,
                [
                    DestinationSearchTool(),
                    LocationTool(),
                    WeatherTool(),
                    RoutingTool(),
                ],
            ),
        )

    def _build_hotel_transport_specialist(self) -> Agent:
        return self._agent(
            role="Hotel and Transport Specialist",
            goal=(
                "Find suitable accommodation and intercity transport options, "
                "compare costs and travel duration, and provide practical "
                "options that respect the customer's preferences."
            ),
            backstory=(
                "You specialize in accommodation and mobility planning. You "
                "clearly label prototype inventory as mock data, preserve "
                "provider information, and use routing estimates to identify "
                "practical travel arrangements."
            ),
            tools=self._tools(
                self.HOTEL_TRANSPORT_SPECIALIST,
                [
                    HotelSearchTool(),
                    TransportSearchTool(),
                    RoutingTool(),
                ],
            ),
        )

    def _build_budget_analyst(self) -> Agent:
        return self._agent(
            role="Travel Budget Analyst",
            goal=(
                "Calculate verified travel expenses, compare the estimated "
                "total with the customer's budget, and identify the exact "
                "surplus or deficit."
            ),
            backstory=(
                "You are a precise travel financial analyst. You never rely "
                "on mental arithmetic or unverified language-model totals. "
                "You use the budget calculator for final calculations and "
                "provide realistic cost-reduction recommendations when the "
                "plan exceeds the available budget."
            ),
            tools=self._tools(
                self.BUDGET_ANALYST,
                [BudgetCalculatorTool()],
            ),
        )

    def _build_itinerary_planner(self) -> Agent:
        return self._agent(
            role="Itinerary Planner",
            goal=(
                "Convert approved research and verified budget findings into "
                "a practical day-by-day itinerary without activity conflicts."
            ),
            backstory=(
                "You design structured travel schedules with realistic dates, "
                "times, locations, costs, and travel order. You validate the "
                "schedule for overlaps and use routing estimates when needed "
                "to keep each day practical."
            ),
            tools=self._tools(
                self.ITINERARY_PLANNER,
                [
                    ItineraryScheduleValidatorTool(),
                    RoutingTool(),
                ],
            ),
        )

    def _validate_agents(self, agents: dict[str, Agent]) -> None:
        """Validate required agents and unique roles."""

        if set(agents) != self.EXPECTED_AGENT_KEYS:
            raise CrewConfigurationError(
                "The travel crew must contain exactly five required agents."
            )

        roles = [agent.role for agent in agents.values()]

        if len(roles) != len(set(roles)):
            raise CrewConfigurationError("Every travel agent must have a unique role.")
