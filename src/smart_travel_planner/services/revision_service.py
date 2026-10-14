"""Deterministic budget revision for over-budget travel plans."""

from decimal import Decimal

from smart_travel_planner.config.settings import get_settings
from smart_travel_planner.models import (
    CustomerTravelRequest,
    FinalTravelPlanOutput,
    RevisionOutcome,
    RevisionRecord,
)


class BudgetRevisionService:
    """Select cheaper options and recalculate without LLM arithmetic."""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()

    def revise(
        self,
        request: CustomerTravelRequest,
        travel_plan: FinalTravelPlanOutput,
    ):
        """Apply bounded deterministic revisions to an over-budget plan."""

        current_plan = travel_plan.model_copy(deep=True)
        revisions = []

        for revision_number in range(
            1,
            self.settings.max_revision_rounds + 1,
        ):
            if current_plan.budget_analysis.within_budget:
                break

            revised = self._apply_cheapest_options(
                request=request,
                travel_plan=current_plan,
                revision_number=revision_number,
            )

            if revised is None:
                break

            current_plan, record = revised
            revisions.append(record)

        exhausted = (
            not current_plan.budget_analysis.within_budget
            and len(revisions) >= self.settings.max_revision_rounds
        )

        return RevisionOutcome(
            travel_plan=current_plan,
            revisions=revisions,
            exhausted=exhausted,
        )

    def _apply_cheapest_options(
        self,
        request,
        travel_plan,
        revision_number,
    ):
        hotel_transport = travel_plan.hotel_transport
        budget = travel_plan.budget_analysis

        original_hotel_cost = Decimal(hotel_transport.estimated_accommodation_cost)
        original_transport_cost = Decimal(hotel_transport.estimated_transport_cost)

        cheapest_hotel = self._cheapest_option(
            hotel_transport.hotels,
            original_hotel_cost,
        )
        cheapest_transport = self._cheapest_option(
            hotel_transport.transport_options,
            original_transport_cost,
        )

        revised_hotel_cost = self._option_cost(
            cheapest_hotel,
            original_hotel_cost,
        )
        revised_transport_cost = self._option_cost(
            cheapest_transport,
            original_transport_cost,
        )

        if (
            revised_hotel_cost >= original_hotel_cost
            and revised_transport_cost >= original_transport_cost
        ):
            return None

        fixed_subtotal = Decimal(budget.subtotal) - original_hotel_cost - original_transport_cost

        revised_subtotal = (fixed_subtotal + revised_hotel_cost + revised_transport_cost).quantize(
            Decimal("0.01")
        )

        contingency_rate = self._contingency_rate(
            subtotal=Decimal(budget.subtotal),
            contingency=Decimal(budget.contingency_amount),
        )

        revised_contingency = (revised_subtotal * contingency_rate).quantize(Decimal("0.01"))

        revised_total = (revised_subtotal + revised_contingency).quantize(Decimal("0.01"))

        customer_budget = Decimal(request.total_budget)
        difference = (customer_budget - revised_total).quantize(Decimal("0.01"))

        within_budget = revised_total <= customer_budget
        original_total = Decimal(budget.estimated_total)
        savings = max(
            Decimal("0.00"),
            original_total - revised_total,
        ).quantize(Decimal("0.01"))

        current_plan = travel_plan.model_copy(deep=True)

        current_plan.hotel_transport.estimated_accommodation_cost = revised_hotel_cost
        current_plan.hotel_transport.estimated_transport_cost = revised_transport_cost
        current_plan.hotel_transport.selected_hotel = cheapest_hotel
        current_plan.hotel_transport.selected_transport = cheapest_transport

        current_plan.budget_analysis.subtotal = revised_subtotal
        current_plan.budget_analysis.contingency_amount = revised_contingency
        current_plan.budget_analysis.estimated_total = revised_total
        current_plan.budget_analysis.customer_budget = customer_budget
        current_plan.budget_analysis.difference = difference
        current_plan.budget_analysis.within_budget = within_budget
        current_plan.budget_analysis.status = "within_budget" if within_budget else "over_budget"

        current_plan.itinerary.estimated_total = revised_total
        current_plan.itinerary.budget_status = "within_budget" if within_budget else "over_budget"
        current_plan.approved = within_budget

        hotel_name = self._option_label(
            cheapest_hotel,
            "name",
        )
        transport_name = self._option_label(
            cheapest_transport,
            "operator",
        )

        record = RevisionRecord(
            revision_number=revision_number,
            original_total=original_total,
            revised_total=revised_total,
            savings_achieved=savings,
            original_hotel_cost=original_hotel_cost,
            revised_hotel_cost=revised_hotel_cost,
            original_transport_cost=original_transport_cost,
            revised_transport_cost=revised_transport_cost,
            remaining_difference=difference,
            selected_hotel=hotel_name,
            selected_transport=transport_name,
            reason=(
                "Selected lower-cost hotel and transport options while "
                "preserving the original destination and travel dates."
            ),
        )

        return current_plan, record

    @staticmethod
    def _cheapest_option(options, current_cost):
        valid_options = []

        for option in options:
            try:
                cost = Decimal(str(option.get("total_cost")))
            except (AttributeError, TypeError, ValueError):
                continue

            if cost >= 0 and cost < current_cost:
                valid_options.append((cost, option))

        if not valid_options:
            return None

        return min(valid_options, key=lambda item: item[0])[1]

    @staticmethod
    def _option_cost(option, fallback):
        if option is None:
            return fallback

        return Decimal(str(option["total_cost"])).quantize(Decimal("0.01"))

    @staticmethod
    def _option_label(option, field):
        if option is None:
            return None

        value = option.get(field)
        return str(value) if value is not None else None

    @staticmethod
    def _contingency_rate(subtotal, contingency):
        if subtotal <= 0:
            return Decimal("0.00")

        return contingency / subtotal
