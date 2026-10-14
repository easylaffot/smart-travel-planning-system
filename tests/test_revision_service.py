"""Tests for deterministic over-budget revision."""

from decimal import Decimal

from smart_travel_planner.config.settings import Settings
from smart_travel_planner.models import WorkflowStatus
from smart_travel_planner.services import (
    BudgetRevisionService,
    FakeCrewRunner,
    TravelPlanningService,
)
from tests.phase4_fixtures import (
    make_customer_request,
    make_execution_result,
    make_final_plan,
)


def make_revision_service(max_rounds=2):
    settings = Settings(
        _env_file=None,
        app_env="test",
        max_revision_rounds=max_rounds,
    )
    return BudgetRevisionService(settings=settings)


def add_cheaper_options(plan):
    plan.hotel_transport.hotels = [
        {
            "name": "Original Hotel",
            "total_cost": "30000.00",
            "data_mode": "mock",
        },
        {
            "name": "Budget Hotel",
            "total_cost": "18000.00",
            "data_mode": "mock",
        },
    ]

    plan.hotel_transport.transport_options = [
        {
            "operator": "Original Flight",
            "mode": "flight",
            "total_cost": "20000.00",
            "data_mode": "mock",
        },
        {
            "operator": "Budget Train",
            "mode": "train",
            "total_cost": "8000.00",
            "data_mode": "mock",
        },
    ]

    plan.hotel_transport.estimated_accommodation_cost = Decimal("30000.00")
    plan.hotel_transport.estimated_transport_cost = Decimal("20000.00")

    return plan


def test_revision_selects_cheaper_options() -> None:
    request = make_customer_request()
    plan = add_cheaper_options(make_final_plan(within_budget=False))

    outcome = make_revision_service().revise(request, plan)

    assert outcome.revision_count == 1
    assert outcome.travel_plan.hotel_transport.selected_hotel["name"] == ("Budget Hotel")
    assert outcome.travel_plan.hotel_transport.selected_transport["operator"] == "Budget Train"
    assert outcome.revisions[0].savings_achieved > Decimal("0.00")


def test_revision_preserves_customer_dates() -> None:
    request = make_customer_request()
    plan = add_cheaper_options(make_final_plan(within_budget=False))

    original_start = plan.itinerary.start_date
    original_end = plan.itinerary.end_date

    outcome = make_revision_service().revise(request, plan)

    assert outcome.travel_plan.itinerary.start_date == original_start
    assert outcome.travel_plan.itinerary.end_date == original_end


def test_no_available_savings_returns_no_revision() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=False)

    outcome = make_revision_service().revise(request, plan)

    assert outcome.revision_count == 0
    assert outcome.travel_plan.budget_analysis.within_budget is False


def test_planning_service_applies_revision() -> None:
    request = make_customer_request()
    plan = add_cheaper_options(make_final_plan(within_budget=False))

    runner_result = make_execution_result(within_budget=False)
    runner_result.structured_output = plan

    service = TravelPlanningService(
        runner=FakeCrewRunner(runner_result),
        revision_service=make_revision_service(),
    )

    result = service.create_plan(request)

    assert result.revision_count == 1
    assert result.status in {
        WorkflowStatus.COMPLETED_AFTER_REVISION,
        WorkflowStatus.COMPLETED_OVER_BUDGET,
    }
    assert result.travel_plan is not None


def test_revision_is_bounded_by_configured_rounds() -> None:
    request = make_customer_request()
    plan = add_cheaper_options(make_final_plan(within_budget=False))

    outcome = make_revision_service(max_rounds=1).revise(
        request,
        plan,
    )

    assert outcome.revision_count <= 1
