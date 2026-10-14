"""Tests for structured outputs exchanged between agents."""

from datetime import date
from decimal import Decimal

from smart_travel_planner.models import (
    BudgetAnalysisOutput,
    DestinationResearchOutput,
    FinalTravelPlanOutput,
    HotelTransportOutput,
    ItineraryPlanOutput,
)


def test_budget_output_serializes_decimal_values() -> None:
    """Monetary values should serialize predictably as JSON strings."""

    output = BudgetAnalysisOutput(
        subtotal=Decimal("50000.00"),
        contingency_amount=Decimal("2500.00"),
        estimated_total=Decimal("52500.00"),
        customer_budget=Decimal("60000.00"),
        difference=Decimal("7500.00"),
        within_budget=True,
        status="within_budget",
        currency="inr",
    )

    serialized = output.model_dump(mode="json")

    assert serialized["estimated_total"] == "52500.00"
    assert serialized["difference"] == "7500.00"
    assert serialized["currency"] == "INR"


def test_final_travel_plan_contains_specialist_outputs() -> None:
    """The final plan should preserve all specialist results."""

    destination = DestinationResearchOutput(
        destination="Jaipur",
        attractions=[],
        data_modes=["mock"],
    )

    hotel_transport = HotelTransportOutput(
        estimated_accommodation_cost=Decimal("16800.00"),
        estimated_transport_cost=Decimal("15600.00"),
        currency="INR",
        data_modes=["mock"],
    )

    budget = BudgetAnalysisOutput(
        subtotal=Decimal("52400.00"),
        contingency_amount=Decimal("2620.00"),
        estimated_total=Decimal("55020.00"),
        customer_budget=Decimal("60000.00"),
        difference=Decimal("4980.00"),
        within_budget=True,
        status="within_budget",
        currency="INR",
    )

    itinerary = ItineraryPlanOutput(
        destination="Jaipur",
        start_date=date(2026, 12, 10),
        end_date=date(2026, 12, 13),
        day_schedules=[],
        estimated_total=Decimal("55020.00"),
        budget_status="within_budget",
    )

    final_plan = FinalTravelPlanOutput(
        destination_research=destination,
        hotel_transport=hotel_transport,
        budget_analysis=budget,
        itinerary=itinerary,
        approved=True,
    )

    assert final_plan.approved is True
    assert final_plan.itinerary.destination == "Jaipur"
    assert final_plan.budget_analysis.within_budget is True
