"""Reusable offline fixtures for Phase 4 tests."""

from datetime import date, timedelta
from decimal import Decimal

from smart_travel_planner.models import (
    Activity,
    BudgetAnalysisOutput,
    CrewExecutionResult,
    CustomerTravelRequest,
    DestinationResearchOutput,
    FinalTravelPlanOutput,
    HotelTransportOutput,
    ItineraryPlanOutput,
)


def make_customer_request() -> CustomerTravelRequest:
    start = date.today() + timedelta(days=30)

    return CustomerTravelRequest(
        starting_location="Mumbai",
        destination="Jaipur",
        start_date=start,
        end_date=start + timedelta(days=3),
        travellers=2,
        total_budget=Decimal("60000.00"),
        currency="INR",
        interests=[
            Activity.SIGHTSEEING,
            Activity.SHOPPING,
            Activity.LOCAL_FOOD,
        ],
        accommodation_preference="mid_range",
        transport_preference="flight",
    )


def make_final_plan(
    within_budget: bool = True,
) -> FinalTravelPlanOutput:
    estimated_total = Decimal("55020.00") if within_budget else Decimal("77700.00")

    customer_budget = Decimal("60000.00")
    difference = customer_budget - estimated_total

    return FinalTravelPlanOutput(
        coordination_summary={
            "destination": "Jaipur",
        },
        destination_research=DestinationResearchOutput(
            destination="Jaipur",
            attractions=[],
            local_experiences=[],
            sources=[],
            warnings=[],
            data_modes=["mock"],
        ),
        hotel_transport=HotelTransportOutput(
            hotels=[],
            transport_options=[],
            estimated_accommodation_cost=Decimal("16800.00"),
            estimated_transport_cost=Decimal("15600.00"),
            currency="INR",
            warnings=[],
            data_modes=["mock"],
        ),
        budget_analysis=BudgetAnalysisOutput(
            subtotal=estimated_total,
            contingency_amount=Decimal("0.00"),
            estimated_total=estimated_total,
            customer_budget=customer_budget,
            difference=difference,
            within_budget=within_budget,
            status=("within_budget" if within_budget else "over_budget"),
            currency="INR",
        ),
        itinerary=ItineraryPlanOutput(
            destination="Jaipur",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=33),
            day_schedules=[],
            estimated_total=estimated_total,
            budget_status=("within_budget" if within_budget else "over_budget"),
            sources=[],
            warnings=[],
        ),
        approved=within_budget,
        validation_warnings=[],
    )


def make_execution_result(
    within_budget: bool = True,
) -> CrewExecutionResult:
    return CrewExecutionResult(
        structured_output=make_final_plan(within_budget),
        metadata={
            "runner": "fake",
        },
    )
