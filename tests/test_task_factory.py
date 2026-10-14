"""Offline tests for travel task definitions and dependencies."""

from crewai import LLM, Task

from smart_travel_planner.agents import TravelAgentFactory
from smart_travel_planner.config.settings import Settings
from smart_travel_planner.crew import TravelTaskFactory
from smart_travel_planner.models import (
    BudgetAnalysisOutput,
    CoordinationPlan,
    DestinationResearchOutput,
    FinalTravelPlanOutput,
    HotelTransportOutput,
    ItineraryPlanOutput,
)


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        crew_verbose=False,
        crew_cache_enabled=False,
    )


def make_llm() -> LLM:
    return LLM(
        model="ollama/offline-test",
        base_url="http://localhost:11434",
        api_key="offline-test-key",
        temperature=0.0,
        max_tokens=256,
    )


def make_tasks() -> dict[str, Task]:
    agents = TravelAgentFactory(
        llm=make_llm(),
        settings=make_settings(),
    ).build()

    return TravelTaskFactory(agents).build()


def context_ids(task: Task) -> set[int]:
    """Return object for the task context dependencies."""

    return {id(item) for item in task.context or []}


def test_task_factory_creates_six_tasks() -> None:
    tasks = make_tasks()

    assert len(tasks) == 6
    assert tuple(tasks) == TravelTaskFactory.EXPECTED_TASK_KEYS


def test_tasks_have_structured_output_models() -> None:
    tasks = make_tasks()

    expected_models = {
        TravelTaskFactory.COORDINATION: CoordinationPlan,
        TravelTaskFactory.DESTINATION_RESEARCH: (DestinationResearchOutput),
        TravelTaskFactory.HOTEL_TRANSPORT_RESEARCH: (HotelTransportOutput),
        TravelTaskFactory.BUDGET_ANALYSIS: BudgetAnalysisOutput,
        TravelTaskFactory.ITINERARY_PLANNING: ItineraryPlanOutput,
        TravelTaskFactory.FINAL_REVIEW: FinalTravelPlanOutput,
    }

    for key, output_model in expected_models.items():
        assert tasks[key].output_pydantic is output_model


def test_destination_and_hotel_tasks_use_coordination_context() -> None:
    tasks = make_tasks()
    coordination = tasks[TravelTaskFactory.COORDINATION]

    assert context_ids(tasks[TravelTaskFactory.DESTINATION_RESEARCH]) == {id(coordination)}

    assert context_ids(tasks[TravelTaskFactory.HOTEL_TRANSPORT_RESEARCH]) == {id(coordination)}


def test_budget_task_has_required_context() -> None:
    tasks = make_tasks()

    expected = {
        id(tasks[TravelTaskFactory.COORDINATION]),
        id(tasks[TravelTaskFactory.DESTINATION_RESEARCH]),
        id(tasks[TravelTaskFactory.HOTEL_TRANSPORT_RESEARCH]),
    }

    assert context_ids(tasks[TravelTaskFactory.BUDGET_ANALYSIS]) == expected


def test_itinerary_task_has_required_context() -> None:
    tasks = make_tasks()

    expected = {
        id(tasks[TravelTaskFactory.COORDINATION]),
        id(tasks[TravelTaskFactory.DESTINATION_RESEARCH]),
        id(tasks[TravelTaskFactory.HOTEL_TRANSPORT_RESEARCH]),
        id(tasks[TravelTaskFactory.BUDGET_ANALYSIS]),
    }

    assert context_ids(tasks[TravelTaskFactory.ITINERARY_PLANNING]) == expected


def test_final_review_has_all_previous_tasks_as_context() -> None:
    tasks = make_tasks()

    expected = {
        id(tasks[TravelTaskFactory.COORDINATION]),
        id(tasks[TravelTaskFactory.DESTINATION_RESEARCH]),
        id(tasks[TravelTaskFactory.HOTEL_TRANSPORT_RESEARCH]),
        id(tasks[TravelTaskFactory.BUDGET_ANALYSIS]),
        id(tasks[TravelTaskFactory.ITINERARY_PLANNING]),
    }

    assert context_ids(tasks[TravelTaskFactory.FINAL_REVIEW]) == expected


def test_no_task_requires_human_input() -> None:
    tasks = make_tasks()

    assert all(task.human_input is False for task in tasks.values())
