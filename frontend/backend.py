"""Frontend bridge to the Phase 4 travel-planning workflow."""

from datetime import time
from decimal import Decimal
from typing import Any

from smart_travel_planner.config.settings import Settings, get_settings
from smart_travel_planner.crew import TravelCrewFactory
from smart_travel_planner.models import (
    BudgetAnalysisOutput,
    CrewExecutionResult,
    CustomerTravelRequest,
    DestinationResearchOutput,
    FinalTravelPlanOutput,
    HotelTransportOutput,
    ItineraryPlanOutput,
)
from smart_travel_planner.providers import MockTravelProvider
from smart_travel_planner.services import (
    FakeCrewRunner,
    LiveCrewRunner,
    TravelPlanningService,
)
from smart_travel_planner.storage import PlanRepository
from smart_travel_planner.workflow import TravelPlanningWorkflow


def live_mode_available(
    settings: Settings | None = None,
) -> bool:
    """Return whether Ollama Cloud is safely configured."""

    active_settings = settings or get_settings()
    return active_settings.ollama_is_configured()


def build_live_workflow(
    settings: Settings | None = None,
) -> TravelPlanningWorkflow:
    """Build the real CrewAI workflow without executing it."""

    active_settings = settings or get_settings()

    crew = TravelCrewFactory(
        settings=active_settings,
    ).build()

    runner = LiveCrewRunner(crew)
    planning_service = TravelPlanningService(runner=runner)

    repository = PlanRepository("data/travel_plans.db")

    return TravelPlanningWorkflow(
        planning_service=planning_service,
        repository=repository,
    )


def build_demo_workflow(
    request: CustomerTravelRequest,
) -> TravelPlanningWorkflow:
    """Build a deterministic offline workflow for dashboard testing."""

    plan = build_demo_plan(request)

    runner = FakeCrewRunner(
        CrewExecutionResult(
            structured_output=plan,
            metadata={
                "runner": "frontend_demo",
                "live_llm_called": False,
            },
        )
    )

    planning_service = TravelPlanningService(runner=runner)

    repository = PlanRepository("data/travel_plans.db")

    return TravelPlanningWorkflow(
        planning_service=planning_service,
        repository=repository,
    )


def build_demo_plan(
    request: CustomerTravelRequest,
) -> FinalTravelPlanOutput:
    """Create a structured tool-derived demonstration plan."""

    provider = MockTravelProvider()

    hotels = provider.find_hotels(
        destination=request.destination,
        nights=max(1, request.duration_days - 1),
        travellers=request.travellers,
        preference=request.accommodation_preference.value,
        currency=request.currency,
    )

    transport_options = provider.find_transport(
        origin=request.starting_location,
        destination=request.destination,
        travellers=request.travellers,
        preferred_mode=request.transport_preference,
        currency=request.currency,
    )

    selected_hotel = min(
        hotels,
        key=lambda option: option.total_cost,
    )

    selected_transport = min(
        transport_options,
        key=lambda option: option.total_cost,
    )

    hotel_cost = selected_hotel.total_cost
    transport_cost = selected_transport.total_cost

    local_transport = Decimal("3500.00")
    attractions = Decimal("4500.00")
    food = Decimal("7000.00")
    shopping = Decimal("2500.00")
    miscellaneous = Decimal("1500.00")

    subtotal = (
        hotel_cost
        + transport_cost
        + local_transport
        + attractions
        + food
        + shopping
        + miscellaneous
    ).quantize(Decimal("0.01"))

    contingency = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))

    estimated_total = (subtotal + contingency).quantize(Decimal("0.01"))

    customer_budget = request.total_budget

    difference = (customer_budget - estimated_total).quantize(Decimal("0.01"))

    within_budget = estimated_total <= customer_budget
    budget_status = "within_budget" if within_budget else "over_budget"

    hotel_dicts = [option.model_dump(mode="json") for option in hotels]

    transport_dicts = [option.model_dump(mode="json") for option in transport_options]

    schedule = _build_demo_schedule(request)

    return FinalTravelPlanOutput(
        coordination_summary={
            "starting_location": request.starting_location,
            "destination": request.destination,
            "duration_days": request.duration_days,
            "travellers": request.travellers,
            "interests": [interest.value for interest in request.interests],
            "mode": "offline_demo",
        },
        destination_research=DestinationResearchOutput(
            destination=request.destination,
            attractions=_demo_attractions(request.destination),
            local_experiences=_demo_experiences(request.destination),
            weather_summary={
                "status": "unavailable",
                "message": ("Live weather is not requested in offline demo mode."),
            },
            routing_notes=[("Travel-time details are estimates in offline demo mode.")],
            sources=[],
            warnings=[
                ("Destination recommendations are demonstration data, not current web research.")
            ],
            data_modes=["mock", "unavailable"],
        ),
        hotel_transport=HotelTransportOutput(
            hotels=hotel_dicts,
            transport_options=transport_dicts,
            selected_hotel=selected_hotel.model_dump(mode="json"),
            selected_transport=selected_transport.model_dump(mode="json"),
            estimated_accommodation_cost=hotel_cost,
            estimated_transport_cost=transport_cost,
            currency=request.currency,
            sources=[],
            warnings=[
                (
                    "Hotel and transport prices are prototype mock "
                    "data and are not live booking offers."
                )
            ],
            data_modes=["mock"],
        ),
        budget_analysis=BudgetAnalysisOutput(
            subtotal=subtotal,
            contingency_amount=contingency,
            estimated_total=estimated_total,
            customer_budget=customer_budget,
            difference=difference,
            within_budget=within_budget,
            status=budget_status,
            cost_reduction_recommendations=(
                []
                if within_budget
                else [
                    "Choose the lowest-cost accommodation option.",
                    "Compare train or bus alternatives.",
                    "Reduce discretionary shopping allocation.",
                ]
            ),
            currency=request.currency,
        ),
        itinerary=ItineraryPlanOutput(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            day_schedules=schedule,
            estimated_total=estimated_total,
            budget_status=budget_status,
            sources=[],
            warnings=[
                (
                    "Schedule entries are generated for frontend "
                    "demonstration and require live verification."
                )
            ],
        ),
        approved=within_budget,
        validation_warnings=[
            (
                "Offline demo mode is active. Mock results are not "
                "live travel or booking information."
            )
        ],
    )


def _build_demo_schedule(
    request: CustomerTravelRequest,
) -> list[dict[str, Any]]:
    """Create one structured schedule per requested trip date."""

    schedules: list[dict[str, Any]] = []

    for index in range(request.duration_days):
        current_date = request.start_date.fromordinal(request.start_date.toordinal() + index)

        if index == 0:
            activities = [
                _activity(
                    "09:00",
                    "11:00",
                    "Arrival and hotel check-in",
                    request.destination,
                    "arrival",
                    "0.00",
                ),
                _activity(
                    "15:00",
                    "18:00",
                    "Orientation and local market visit",
                    request.destination,
                    "shopping",
                    "1000.00",
                ),
            ]
        elif index == request.duration_days - 1:
            activities = [
                _activity(
                    "09:00",
                    "11:00",
                    "Leisure time and final shopping",
                    request.destination,
                    "relaxation",
                    "1000.00",
                ),
                _activity(
                    "13:00",
                    "15:00",
                    "Hotel checkout and departure",
                    request.destination,
                    "departure",
                    "0.00",
                ),
            ]
        else:
            activities = [
                _activity(
                    "09:00",
                    "12:00",
                    "Major destination sightseeing",
                    request.destination,
                    "sightseeing",
                    "1200.00",
                ),
                _activity(
                    "13:30",
                    "16:30",
                    "Cultural and local experience",
                    request.destination,
                    "culture",
                    "900.00",
                ),
                _activity(
                    "18:00",
                    "20:00",
                    "Local dining experience",
                    request.destination,
                    "local_food",
                    "1000.00",
                ),
            ]

        schedules.append(
            {
                "date": current_date.isoformat(),
                "day_number": index + 1,
                "title": f"Day {index + 1}",
                "activities": activities,
            }
        )

    return schedules


def _activity(
    start_time: str,
    end_time: str,
    title: str,
    location: str,
    category: str,
    estimated_cost: str,
) -> dict[str, str]:
    """Return one frontend-friendly itinerary activity."""

    time.fromisoformat(start_time)
    time.fromisoformat(end_time)

    return {
        "start_time": start_time,
        "end_time": end_time,
        "title": title,
        "location": location,
        "category": category,
        "estimated_cost": estimated_cost,
    }


def _demo_attractions(destination: str) -> list[dict[str, str]]:
    """Return labelled demonstration attractions."""

    return [
        {
            "name": f"{destination} heritage district",
            "category": "sightseeing",
            "duration": "3 hours",
            "data_mode": "mock",
        },
        {
            "name": f"{destination} cultural centre",
            "category": "culture",
            "duration": "2 hours",
            "data_mode": "mock",
        },
        {
            "name": f"{destination} central market",
            "category": "shopping",
            "duration": "2 hours",
            "data_mode": "mock",
        },
    ]


def _demo_experiences(
    destination: str,
) -> list[dict[str, str]]:
    """Return labelled demonstration local experiences."""

    return [
        {
            "name": f"Local food experience in {destination}",
            "category": "local_food",
            "data_mode": "mock",
        },
        {
            "name": f"Traditional craft experience in {destination}",
            "category": "culture",
            "data_mode": "mock",
        },
    ]
