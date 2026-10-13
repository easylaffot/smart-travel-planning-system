"""Customer travel request and cross-field validation."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class Activity(StrEnum):
    SIGHTSEEING = "sightseeing"
    SHOPPING = "shopping"
    ADVENTURE = "adventure"
    RELAXATION = "relaxation"
    LOCAL_FOOD = "local_food"
    CULTURE = "culture"
    NATURE = "nature"


class TravelClass(StrEnum):
    BUDGET = "budget"
    MID_RANGE = "mid_range"
    PREMIUM = "premium"


class CustomerTravelRequest(BaseModel):
    """Validated input accepted by the travel-planning workflow."""

    starting_location: str = Field(min_length=2, max_length=120)
    destination: str = Field(min_length=2, max_length=120)
    start_date: date
    end_date: date
    travellers: int = Field(default=1, ge=1, le=20)
    total_budget: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    interests: list[Activity] = Field(min_length=1)
    accommodation_preference: TravelClass = TravelClass.MID_RANGE
    transport_preference: str = Field(default="any", min_length=2, max_length=50)
    special_requirements: str | None = Field(default=None, max_length=1000)

    @field_validator("starting_location", "destination", "transport_preference")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized.isalpha():
            raise ValueError("currency must be a three-letter alphabetic code")
        return normalized

    @field_validator("interests")
    @classmethod
    def unique_interests(cls, value: list[Activity]) -> list[Activity]:
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_trip(self) -> "CustomerTravelRequest":
        if self.start_date < date.today():
            raise ValueError("start_date cannot be in the past")
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if self.starting_location.casefold() == self.destination.casefold():
            raise ValueError("destination must differ from starting_location")
        if self.duration_days > 30:
            raise ValueError("trip duration cannot exceed 30 days in this prototype")
        return self

    @computed_field
    @property
    def duration_days(self) -> int:
        """Inclusive trip duration."""
        return (self.end_date - self.start_date).days + 1
