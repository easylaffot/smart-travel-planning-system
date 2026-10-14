"""Offline tests for the Streamlit backend bridge."""

from frontend.backend import (
    build_demo_plan,
    build_demo_workflow,
)
from smart_travel_planner.models import WorkflowStatus
from tests.phase4_fixtures import make_customer_request


def test_demo_plan_preserves_customer_constraints() -> None:
    """Demo planning must preserve validated customer constraints."""

    request = make_customer_request()

    plan = build_demo_plan(request)

    assert plan.itinerary.destination == request.destination
    assert plan.itinerary.start_date == request.start_date
    assert plan.itinerary.end_date == request.end_date
    assert plan.budget_analysis.customer_budget == request.total_budget
    assert plan.hotel_transport.currency == request.currency
    assert plan.budget_analysis.currency == request.currency


def test_demo_plan_labels_mock_data() -> None:
    """Prototype results must never be presented as live data."""

    request = make_customer_request()

    plan = build_demo_plan(request)

    assert "mock" in plan.destination_research.data_modes
    assert "mock" in plan.hotel_transport.data_modes
    assert plan.validation_warnings


def test_demo_plan_contains_hotel_and_transport_options() -> None:
    """The demo plan should provide structured comparison options."""

    request = make_customer_request()

    plan = build_demo_plan(request)

    assert plan.hotel_transport.hotels
    assert plan.hotel_transport.transport_options
    assert plan.hotel_transport.selected_hotel is not None
    assert plan.hotel_transport.selected_transport is not None


def test_demo_plan_contains_daily_schedule() -> None:
    """The demo itinerary should cover every requested travel day."""

    request = make_customer_request()

    plan = build_demo_plan(request)

    assert len(plan.itinerary.day_schedules) == request.duration_days

    schedule_dates = [day["date"] for day in plan.itinerary.day_schedules]

    assert schedule_dates[0] == request.start_date.isoformat()
    assert schedule_dates[-1] == request.end_date.isoformat()


def test_demo_workflow_runs_without_live_services() -> None:
    """Demo workflow should complete using its injected fake runner."""

    request = make_customer_request()

    result = build_demo_workflow(request).run(request)

    assert result.travel_plan is not None
    assert result.status in {
        WorkflowStatus.COMPLETED_WITHIN_BUDGET,
        WorkflowStatus.COMPLETED_AFTER_REVISION,
        WorkflowStatus.COMPLETED_OVER_BUDGET,
    }
    assert result.application_id.startswith("TRIP-")
    assert not result.errors
