"""Offline tests for Phase 4A planning execution."""

from datetime import date

from smart_travel_planner.models import WorkflowStatus
from smart_travel_planner.services import (
    FakeCrewRunner,
    KickoffInputBuilder,
    TravelPlanningService,
    TravelPlanResultParser,
)
from tests.phase4_fixtures import (
    make_customer_request,
    make_execution_result,
    make_final_plan,
)


def test_input_builder_preserves_validated_request() -> None:
    request = make_customer_request()

    inputs = KickoffInputBuilder().build(request)

    assert inputs["starting_location"] == "Mumbai"
    assert inputs["destination"] == "Jaipur"
    assert inputs["start_date"] == request.start_date.isoformat()
    assert inputs["end_date"] == request.end_date.isoformat()
    assert date.fromisoformat(inputs["start_date"]) == request.start_date
    assert date.fromisoformat(inputs["end_date"]) == request.end_date
    assert inputs["duration_days"] == 4
    assert inputs["travellers"] == 2
    assert inputs["total_budget"] == "60000.00"
    assert inputs["currency"] == "INR"
    assert inputs["transport_preference"] == "flight"


def test_result_parser_accepts_structured_result() -> None:
    expected = make_final_plan()
    execution = make_execution_result()

    result = TravelPlanResultParser().parse(execution)

    assert result == expected
    assert result.budget_analysis.within_budget is True


def test_result_parser_accepts_json_string() -> None:
    expected = make_final_plan()
    raw = expected.model_dump_json()

    result = TravelPlanResultParser().parse(raw)

    assert result.destination_research.destination == "Jaipur"
    assert result.budget_analysis.estimated_total == expected.budget_analysis.estimated_total


def test_planning_service_returns_within_budget_status() -> None:
    request = make_customer_request()
    runner = FakeCrewRunner(make_execution_result(within_budget=True))

    result = TravelPlanningService(runner).create_plan(request)

    assert result.status == WorkflowStatus.COMPLETED_WITHIN_BUDGET
    assert result.travel_plan is not None
    assert result.travel_plan.budget_analysis.within_budget is True
    assert runner.call_count == 1
    assert runner.last_inputs is not None
    assert runner.last_inputs["destination"] == "Jaipur"


def test_planning_service_returns_over_budget_status() -> None:
    request = make_customer_request()
    runner = FakeCrewRunner(make_execution_result(within_budget=False))

    result = TravelPlanningService(runner).create_plan(request)

    assert result.status == WorkflowStatus.COMPLETED_OVER_BUDGET
    assert result.travel_plan is not None
    assert result.travel_plan.budget_analysis.within_budget is False
    assert result.revision_count == 0
