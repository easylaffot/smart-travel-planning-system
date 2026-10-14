"""Structured outputs exchanged between CrewAI travel agents."""

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CoordinationPlan(BaseModel):
    """Coordinator interpretation of the customer request."""

    interpreted_requirements: dict[str, Any] = Field(default_factory=dict)
    research_priorities: list[str] = Field(default_factory=list)
    budget_constraints: dict[str, Any] = Field(default_factory=dict)
    required_specialists: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DestinationResearchOutput(BaseModel):
    """Destination information gathered through research tools."""

    destination: str
    attractions: list[dict[str, Any]] = Field(default_factory=list)
    local_experiences: list[dict[str, Any]] = Field(default_factory=list)
    weather_summary: dict[str, Any] | None = None
    routing_notes: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    data_modes: list[str] = Field(default_factory=list)


class HotelTransportOutput(BaseModel):
    """Accommodation and transport research output."""

    hotels: list[dict[str, Any]] = Field(default_factory=list)
    transport_options: list[dict[str, Any]] = Field(default_factory=list)
    selected_hotel: dict[str, Any] | None = None
    selected_transport: dict[str, Any] | None = None
    estimated_accommodation_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )
    estimated_transport_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )
    currency: str = Field(default="INR", min_length=3, max_length=3)
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    data_modes: list[str] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize ISO-style currency codes."""

        return value.strip().upper()


class BudgetAnalysisOutput(BaseModel):
    """Verified result produced by the budget analyst."""

    subtotal: Decimal = Field(ge=0)
    contingency_amount: Decimal = Field(ge=0)
    estimated_total: Decimal = Field(ge=0)
    customer_budget: Decimal = Field(gt=0)
    difference: Decimal
    within_budget: bool
    status: str
    cost_reduction_recommendations: list[str] = Field(default_factory=list)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize ISO-style currency codes."""

        return value.strip().upper()


class ItineraryPlanOutput(BaseModel):
    """Structured day-by-day itinerary prepared for final review."""

    destination: str
    start_date: date
    end_date: date
    day_schedules: list[dict[str, Any]] = Field(default_factory=list)
    estimated_total: Decimal = Field(ge=0)
    budget_status: str
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FinalTravelPlanOutput(BaseModel):
    """Coordinator-approved final travel-plan response."""

    coordination_summary: dict[str, Any] = Field(default_factory=dict)
    destination_research: DestinationResearchOutput
    hotel_transport: HotelTransportOutput
    budget_analysis: BudgetAnalysisOutput
    itinerary: ItineraryPlanOutput
    approved: bool
    validation_warnings: list[str] = Field(default_factory=list)
