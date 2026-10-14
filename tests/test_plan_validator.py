"""Tests for final travel-plan consistency validation."""

from decimal import Decimal

import pytest

from smart_travel_planner.services import FinalPlanValidator
from smart_travel_planner.utils.exceptions import PlanValidationError
from tests.phase4_fixtures import (
    make_customer_request,
    make_final_plan,
)


def test_valid_plan_returns_non_blocking_warnings() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)

    warnings = FinalPlanValidator().validate(request, plan)

    assert isinstance(warnings, list)


def test_destination_mismatch_is_rejected() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)
    plan.itinerary.destination = "Udaipur"

    with pytest.raises(
        PlanValidationError,
        match="Destination",
    ):
        FinalPlanValidator().validate(request, plan)


def test_date_change_is_rejected() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)
    plan.itinerary.start_date = request.end_date

    with pytest.raises(
        PlanValidationError,
        match="start date",
    ):
        FinalPlanValidator().validate(request, plan)


def test_inconsistent_budget_difference_is_rejected() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)
    plan.budget_analysis.difference = Decimal("99999.00")

    with pytest.raises(
        PlanValidationError,
        match="difference",
    ):
        FinalPlanValidator().validate(request, plan)


def test_mock_data_produces_warning() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)

    warnings = FinalPlanValidator().validate(request, plan)

    assert any("mock data" in warning for warning in warnings)
