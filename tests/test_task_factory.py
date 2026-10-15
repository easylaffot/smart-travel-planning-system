"""Offline tests for travel task definitions and dependencies."""

import socket

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
from smart_travel_planner.services import KickoffInputBuilder
from tests.phase4_fixtures import make_customer_request


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
    itinerary_task = make_tasks()[TravelTaskFactory.ITINERARY_PLANNING]
    assert "real attraction names and routing notes from destination research" in (
        itinerary_task.description
    )


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


def test_budget_task_interpolates_validated_budget() -> None:
    task = make_tasks()[TravelTaskFactory.BUDGET_ANALYSIS]

    task.interpolate_inputs_and_add_conversation_history(
        {
            "destination": "Jaipur",
            "start_date": "2030-01-01",
            "end_date": "2030-01-04",
            "duration_days": 4,
            "starting_location": "Mumbai",
            "travellers": 2,
            "total_budget": "60000.00",
            "currency": "INR",
        }
    )

    assert "customer's budget of 60000.00 INR" in task.description
    assert "preserve it as customer_budget" in task.description


def test_every_task_interpolates_hard_customer_constraints() -> None:
    inputs = KickoffInputBuilder().build(make_customer_request())
    tasks = make_tasks()
    required_text = (
        "Customer destination: {destination}",
        "Trip start date: {start_date}",
        "Trip end date: {end_date}",
        "Trip duration: {duration_days} days",
        "Starting location: {starting_location}",
        "Travellers: {travellers}",
        "Budget: {total_budget} {currency}",
        "Never alter destination, start_date, end_date, or duration_days.",
        "Copy dates exactly in ISO YYYY-MM-DD format.",
        "The destination_research.destination field must equal {destination}.",
        "The itinerary.destination field must equal {destination}.",
        "The itinerary.start_date field must equal {start_date}.",
        "The itinerary.end_date field must equal {end_date}.",
    )

    for task in tasks.values():
        assert all(text in task.description for text in required_text)
        task.interpolate_inputs_and_add_conversation_history(inputs)
        assert f"Customer destination: {inputs['destination']}" in task.description
        assert f"Trip start date: {inputs['start_date']}" in task.description
        assert f"Trip end date: {inputs['end_date']}" in task.description
        assert f"Budget: {inputs['total_budget']} {inputs['currency']}" in task.description


def test_destination_research_requires_search_tool_and_structured_records() -> None:
    task = make_tasks()[TravelTaskFactory.DESTINATION_RESEARCH]

    assert "must call the assigned DestinationSearchTool" in task.description
    assert "(destination_search) with result_limit=8" in task.description
    assert "at least 3 attraction records and 2 local-experience records" in task.description
    assert "Every record must contain name, category, and data_mode." in task.description
    assert "Empty lists are allowed only when the tool explicitly returns status unavailable." in (
        task.description
    )


def test_task_factory_builds_without_network(monkeypatch) -> None:
    def reject_network(*args, **kwargs):
        raise AssertionError("Task construction must not make network requests")

    monkeypatch.setattr(socket.socket, "connect", reject_network)

    assert len(make_tasks()) == 6


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
