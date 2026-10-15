"""Factory for structured CrewAI travel-planning tasks."""

from crewai import Agent, Task

from smart_travel_planner.agents import TravelAgentFactory
from smart_travel_planner.models import (
    BudgetAnalysisOutput,
    CoordinationPlan,
    DestinationResearchOutput,
    FinalTravelPlanOutput,
    HotelTransportOutput,
    ItineraryPlanOutput,
)
from smart_travel_planner.utils.exceptions import CrewConfigurationError

_CUSTOMER_CONSTRAINTS = (
    "Customer destination: {destination}\n"
    "Trip start date: {start_date}\n"
    "Trip end date: {end_date}\n"
    "Trip duration: {duration_days} days\n"
    "Starting location: {starting_location}\n"
    "Travellers: {travellers}\n"
    "Budget: {total_budget} {currency}\n"
    "Hard constraints: Never alter destination, start_date, end_date, or "
    "duration_days. Copy dates exactly in ISO YYYY-MM-DD format. The "
    "destination_research.destination field must equal {destination}. The "
    "itinerary.destination field must equal {destination}. The "
    "itinerary.start_date field must equal {start_date}. The "
    "itinerary.end_date field must equal {end_date}.\n\n"
)


class TravelTaskFactory:
    """Create the six tasks and their explicit dependencies."""

    COORDINATION = "requirements_coordination"
    DESTINATION_RESEARCH = "destination_research"
    HOTEL_TRANSPORT_RESEARCH = "hotel_transport_research"
    BUDGET_ANALYSIS = "budget_analysis"
    ITINERARY_PLANNING = "itinerary_planning"
    FINAL_REVIEW = "final_coordinator_review"

    EXPECTED_TASK_KEYS = (
        COORDINATION,
        DESTINATION_RESEARCH,
        HOTEL_TRANSPORT_RESEARCH,
        BUDGET_ANALYSIS,
        ITINERARY_PLANNING,
        FINAL_REVIEW,
    )

    def __init__(self, agents: dict[str, Agent]) -> None:
        self.agents = agents
        self._validate_agents()

    def build(self) -> dict[str, Task]:
        """Build all tasks in sequential execution order."""

        coordination = self._coordination_task()

        destination_research = self._destination_research_task(
            coordination=coordination,
        )

        hotel_transport = self._hotel_transport_task(
            coordination=coordination,
        )

        budget_analysis = self._budget_analysis_task(
            coordination=coordination,
            destination_research=destination_research,
            hotel_transport=hotel_transport,
        )

        itinerary_planning = self._itinerary_planning_task(
            coordination=coordination,
            destination_research=destination_research,
            hotel_transport=hotel_transport,
            budget_analysis=budget_analysis,
        )

        final_review = self._final_review_task(
            coordination=coordination,
            destination_research=destination_research,
            hotel_transport=hotel_transport,
            budget_analysis=budget_analysis,
            itinerary_planning=itinerary_planning,
        )

        tasks = {
            self.COORDINATION: coordination,
            self.DESTINATION_RESEARCH: destination_research,
            self.HOTEL_TRANSPORT_RESEARCH: hotel_transport,
            self.BUDGET_ANALYSIS: budget_analysis,
            self.ITINERARY_PLANNING: itinerary_planning,
            self.FINAL_REVIEW: final_review,
        }

        self._validate_tasks(tasks)
        return tasks

    def ordered_tasks(self, tasks: dict[str, Task]) -> list[Task]:
        """Return tasks in the required sequential order."""
        return [tasks[key] for key in self.EXPECTED_TASK_KEYS]

    def _coordination_task(self) -> Task:
        return Task(
            description=_CUSTOMER_CONSTRAINTS
            + (
                "Interpret the validated customer travel request supplied "
                "through kickoff inputs. Identify the starting location, "
                "destination, travel dates, duration, traveller count, total "
                "budget, currency, interests, accommodation preference, "
                "transport preference, and special requirements. Create "
                "research priorities and budget constraints for the specialist "
                "agents. Do not invent missing customer data. Clearly include "
                "warnings for incomplete or conflicting requirements."
            ),
            expected_output=(
                "A structured coordination plan containing interpreted "
                "requirements, research priorities, budget constraints, "
                "required specialists, and warnings."
            ),
            agent=self.agents[TravelAgentFactory.COORDINATOR],
            output_pydantic=CoordinationPlan,
            human_input=False,
        )

    def _destination_research_task(
        self,
        *,
        coordination: Task,
    ) -> Task:
        return Task(
            description=_CUSTOMER_CONSTRAINTS
            + (
                "You must call the assigned DestinationSearchTool "
                "(destination_search) with result_limit=8 before drafting "
                "destination recommendations. "
                "Use the returned JSON as the source for attractions and local "
                "experiences. Map its attractions, local_experiences, "
                "routing_notes, and sources into the matching destination "
                "research fields. Preserve each live record's name, category, "
                "description, source_url, duration, and data_mode. When mock "
                "fallback records are present, copy them "
                "into destination_research.attractions and "
                "destination_research.local_experiences without changing their "
                "names, categories, or mock labels. Return at least 3 attraction "
                "records and 2 local-experience records when those fallback "
                "records are available. Every record must contain name, category, "
                "and data_mode. Never present mock data as live or invent live "
                "facts. Empty lists are allowed only when the tool explicitly "
                "returns status unavailable. Using the approved coordination "
                "plan, also research attractions, "
                "local experiences, destination details, available weather, "
                "and useful routing information. Use assigned tools instead "
                "of relying only on general model knowledge. Preserve source "
                "URLs and data-mode labels. Never describe mock results as "
                "live information. Never invent weather when the forecast is "
                "outside the available window. Match recommendations to the "
                "customer's interests, dates, and practical trip duration."
            ),
            expected_output=(
                "Structured destination research containing attractions, "
                "at least 3 mock fallback attraction records and 2 mock fallback "
                "local-experience records when available, available weather, "
                "routing notes, sources, warnings, and data-mode labels."
            ),
            agent=self.agents[TravelAgentFactory.DESTINATION_RESEARCHER],
            context=[coordination],
            output_pydantic=DestinationResearchOutput,
            human_input=False,
        )

    def _hotel_transport_task(
        self,
        *,
        coordination: Task,
    ) -> Task:
        return Task(
            description=_CUSTOMER_CONSTRAINTS
            + (
                "Using the approved coordination plan, find accommodation and "
                "intercity transport options that fit the number of travellers, "
                "trip duration, preferences, and currency. Use the hotel, "
                "transport, and routing tools. Compare relevant options and "
                "select a practical preliminary hotel and transport choice. "
                "Preserve provider and data-mode labels. Explicitly identify "
                "mock inventory as prototype data rather than live booking "
                "availability. Never label hotel prices or transport fares as "
                "live. Use price_mode=estimated and fare_mode=estimated for "
                "calculated amounts. Return tool-derived cost totals."
            ),
            expected_output=(
                "Structured accommodation and transport research containing "
                "options, preliminary selections, estimated costs, currency, "
                "sources, warnings, and data-mode labels."
            ),
            agent=self.agents[TravelAgentFactory.HOTEL_TRANSPORT_SPECIALIST],
            context=[coordination],
            output_pydantic=HotelTransportOutput,
            human_input=False,
        )

    def _budget_analysis_task(
        self,
        *,
        coordination: Task,
        destination_research: Task,
        hotel_transport: Task,
    ) -> Task:
        return Task(
            description=_CUSTOMER_CONSTRAINTS
            + (
                "Analyse the coordinated requirements, researched activities, "
                "hotel options, transport options, local travel, meals, and "
                "other expected expenses. Always use the assigned budget "
                "calculator for final arithmetic. Do not calculate the final "
                "total using language-model arithmetic. Compare the verified "
                "estimated total with the customer's budget of {total_budget} "
                "{currency} from the validated request. Pass that exact budget "
                "to the calculator and preserve it as customer_budget in the "
                "structured output. Report the exact remaining amount or "
                "deficit. If the plan is over budget, "
                "provide specific cost-reduction recommendations for Phase 4 "
                "to evaluate."
            ),
            expected_output=(
                "A verified structured budget analysis containing subtotal, "
                "contingency, estimated total, customer budget, difference, "
                "within-budget status, recommendations, and currency."
            ),
            agent=self.agents[TravelAgentFactory.BUDGET_ANALYST],
            context=[
                coordination,
                destination_research,
                hotel_transport,
            ],
            output_pydantic=BudgetAnalysisOutput,
            human_input=False,
        )

    def _itinerary_planning_task(
        self,
        *,
        coordination: Task,
        destination_research: Task,
        hotel_transport: Task,
        budget_analysis: Task,
    ) -> Task:
        return Task(
            description=_CUSTOMER_CONSTRAINTS
            + (
                "Create a practical day-by-day itinerary using the coordinated "
                "requirements, destination research, hotel and transport "
                "findings, and verified budget analysis. Use real attraction "
                "names and routing notes from destination research when available. "
                "Represent each travel date, order activities chronologically, "
                "include realistic travel time, and avoid schedule conflicts. "
                "Use the schedule "
                "validator before returning the itinerary. Preserve sources, "
                "data limitations, and warnings. Do not silently change the "
                "customer's dates or trip duration."
            ),
            expected_output=(
                "A structured itinerary containing destination, trip dates, "
                "ordered daily schedules, estimated total, budget status, "
                "sources, and warnings."
            ),
            agent=self.agents[TravelAgentFactory.ITINERARY_PLANNER],
            context=[
                coordination,
                destination_research,
                hotel_transport,
                budget_analysis,
            ],
            output_pydantic=ItineraryPlanOutput,
            human_input=False,
        )

    def _final_review_task(
        self,
        *,
        coordination: Task,
        destination_research: Task,
        hotel_transport: Task,
        budget_analysis: Task,
        itinerary_planning: Task,
    ) -> Task:
        return Task(
            description=_CUSTOMER_CONSTRAINTS
            + (
                "Review every specialist output for consistency, completeness, "
                "source preservation, data-mode accuracy, schedule validity, "
                "and budget accuracy. Confirm that mock data is labelled as "
                "mock and unavailable information has not been invented. "
                "Confirm that the itinerary covers all trip dates and reflects "
                "the customer's interests. Do not revise an over-budget plan "
                "inside this task. If the plan is over budget, preserve the "
                "verified deficit and recommendations so the controlled Phase "
                "4 revision workflow can act on them."
            ),
            expected_output=(
                "A coordinator-reviewed final travel plan containing all "
                "specialist outputs, approval status, and validation warnings."
            ),
            agent=self.agents[TravelAgentFactory.COORDINATOR],
            context=[
                coordination,
                destination_research,
                hotel_transport,
                budget_analysis,
                itinerary_planning,
            ],
            output_pydantic=FinalTravelPlanOutput,
            human_input=False,
        )

    def _validate_agents(self) -> None:
        required = TravelAgentFactory.EXPECTED_AGENT_KEYS
        available = set(self.agents)

        if available != required:
            missing = sorted(required - available)
            unexpected = sorted(available - required)

            raise CrewConfigurationError(
                "Invalid agents supplied to TravelTaskFactory. "
                f"Missing={missing}; unexpected={unexpected}."
            )

    def _validate_tasks(self, tasks: dict[str, Task]) -> None:
        if tuple(tasks) != self.EXPECTED_TASK_KEYS:
            raise CrewConfigurationError("Travel tasks are not in the required sequential order.")

        if len({id(task) for task in tasks.values()}) != len(tasks):
            raise CrewConfigurationError("Every travel task must be a distinct Task instance.")
