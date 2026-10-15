"""Tests for final travel-plan consistency validation."""

import logging
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


def test_research_destination_mismatch_is_rejected() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)
    plan.destination_research.destination = "Udaipur"

    with pytest.raises(PlanValidationError, match="Destination"):
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


def test_end_date_change_is_rejected() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)
    plan.itinerary.end_date = request.start_date

    with pytest.raises(PlanValidationError, match="end date"):
        FinalPlanValidator().validate(request, plan)


def test_destination_case_and_surrounding_whitespace_are_accepted() -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)
    plan.destination_research.destination = "  jAiPuR "
    plan.itinerary.destination = " JAIPUR  "

    FinalPlanValidator().validate(request, plan)


def test_validation_logs_requested_and_generated_anchors(caplog) -> None:
    request = make_customer_request()
    plan = make_final_plan(within_budget=True)

    with caplog.at_level(
        logging.INFO,
        logger="smart_travel_planner.services.plan_validator",
    ):
        FinalPlanValidator().validate(request, plan)

    assert f"requested_destination='{request.destination}'" in caplog.text
    assert f"research_destination='{plan.destination_research.destination}'" in caplog.text
    assert f"itinerary_destination='{plan.itinerary.destination}'" in caplog.text
    assert f"requested_start_date={request.start_date.isoformat()}" in caplog.text
    assert f"requested_end_date={request.end_date.isoformat()}" in caplog.text
    assert f"generated_start_date={plan.itinerary.start_date.isoformat()}" in caplog.text
    assert f"generated_end_date={plan.itinerary.end_date.isoformat()}" in caplog.text


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
