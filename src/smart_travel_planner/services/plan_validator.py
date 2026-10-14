"""Final consistency validation for generated travel plans."""

from decimal import Decimal

from smart_travel_planner.models import (
    CustomerTravelRequest,
    FinalTravelPlanOutput,
)
from smart_travel_planner.utils.exceptions import PlanValidationError


class FinalPlanValidator:
    """Validate critical customer constraints and financial consistency."""

    def validate(
        self,
        request: CustomerTravelRequest,
        plan: FinalTravelPlanOutput,
    ) -> list[str]:
        """Validate the final plan and return non-blocking warnings."""

        errors: list[str] = []
        warnings: list[str] = []

        self._validate_destination(request, plan, errors)
        self._validate_dates(request, plan, errors)
        self._validate_currency(request, plan, errors)
        self._validate_budget(request, plan, errors)
        self._validate_schedule(request, plan, errors, warnings)
        self._validate_data_modes(plan, warnings)

        if errors:
            raise PlanValidationError("Final travel plan failed validation: " + "; ".join(errors))

        return warnings

    @staticmethod
    def _validate_destination(
        request: CustomerTravelRequest,
        plan: FinalTravelPlanOutput,
        errors: list[str],
    ) -> None:
        destinations = {
            plan.destination_research.destination.strip().casefold(),
            plan.itinerary.destination.strip().casefold(),
        }

        expected = request.destination.strip().casefold()

        if destinations != {expected}:
            errors.append("Destination research and itinerary must match the customer destination.")

    @staticmethod
    def _validate_dates(
        request: CustomerTravelRequest,
        plan: FinalTravelPlanOutput,
        errors: list[str],
    ) -> None:
        if plan.itinerary.start_date != request.start_date:
            errors.append("Itinerary start date does not match the customer request.")

        if plan.itinerary.end_date != request.end_date:
            errors.append("Itinerary end date does not match the customer request.")

        if plan.itinerary.end_date < plan.itinerary.start_date:
            errors.append("Itinerary end date cannot be before its start date.")

    @staticmethod
    def _validate_currency(
        request: CustomerTravelRequest,
        plan: FinalTravelPlanOutput,
        errors: list[str],
    ) -> None:
        expected = request.currency.strip().upper()

        currencies = {
            plan.hotel_transport.currency.strip().upper(),
            plan.budget_analysis.currency.strip().upper(),
        }

        if currencies != {expected}:
            errors.append(
                "Hotel, transport, and budget currencies must match the customer-request currency."
            )

    @staticmethod
    def _validate_budget(
        request: CustomerTravelRequest,
        plan: FinalTravelPlanOutput,
        errors: list[str],
    ) -> None:
        budget = plan.budget_analysis
        customer_budget = Decimal(request.total_budget)

        if Decimal(budget.customer_budget) != customer_budget:
            errors.append(
                "Budget analysis customer budget does not match the validated customer request."
            )

        expected_difference = (customer_budget - Decimal(budget.estimated_total)).quantize(
            Decimal("0.01")
        )

        if Decimal(budget.difference) != expected_difference:
            errors.append("Budget difference is inconsistent with the estimated total.")

        expected_within_budget = Decimal(budget.estimated_total) <= customer_budget

        if budget.within_budget != expected_within_budget:
            errors.append("Budget status is inconsistent with the estimated total.")

        if Decimal(plan.itinerary.estimated_total) != Decimal(budget.estimated_total):
            errors.append("Itinerary total does not match the verified budget total.")

        expected_status = "within_budget" if expected_within_budget else "over_budget"

        if budget.status != expected_status:
            errors.append("Budget status text is inconsistent with the verified total.")

        if plan.itinerary.budget_status != expected_status:
            errors.append("Itinerary budget status is inconsistent with the budget analysis.")

    @staticmethod
    def _validate_schedule(
        request: CustomerTravelRequest,
        plan: FinalTravelPlanOutput,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        for day in plan.itinerary.day_schedules:
            raw_date = day.get("date")

            if raw_date is None:
                warnings.append("A day schedule is missing its date.")
                continue

            date_value = str(raw_date)

            if not (request.start_date.isoformat() <= date_value <= request.end_date.isoformat()):
                errors.append("An itinerary day falls outside the requested trip dates.")
                break

        if not plan.itinerary.day_schedules:
            warnings.append("The itinerary currently contains no detailed daily schedule entries.")

    @staticmethod
    def _validate_data_modes(
        plan: FinalTravelPlanOutput,
        warnings: list[str],
    ) -> None:
        modes = {
            str(mode).strip().lower()
            for mode in (plan.destination_research.data_modes + plan.hotel_transport.data_modes)
        }

        if "mock" in modes:
            warnings.append("The plan contains clearly labelled prototype mock data.")

        if "unavailable" in modes:
            warnings.append("Some requested live information was unavailable.")
