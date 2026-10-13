"""Structured hotel, transport, and budget models."""

from decimal import Decimal

from pydantic import BaseModel, Field, computed_field, field_validator

from .provider_results import DataMode


class HotelOption(BaseModel):
    """One accommodation option returned by a provider."""

    hotel_id: str
    name: str
    destination: str
    category: str
    price_per_room_per_night: Decimal = Field(gt=0)
    rooms: int = Field(ge=1)
    nights: int = Field(ge=1)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    rating: Decimal = Field(ge=0, le=5)
    amenities: list[str] = Field(default_factory=list)
    data_mode: DataMode = DataMode.MOCK
    provider: str = "mock_hotel_provider"
    source_url: str | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @computed_field
    @property
    def total_cost(self) -> Decimal:
        return (
            self.price_per_room_per_night * Decimal(self.rooms) * Decimal(self.nights)
        ).quantize(Decimal("0.01"))


class TransportOption(BaseModel):
    """One intercity transport option."""

    transport_id: str
    mode: str
    operator: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration_minutes: int = Field(gt=0)
    price_per_person: Decimal = Field(gt=0)
    travellers: int = Field(ge=1)
    trip_type: str = "round_trip"
    currency: str = Field(default="INR", min_length=3, max_length=3)
    data_mode: DataMode = DataMode.MOCK
    provider: str = "mock_transport_provider"
    source_url: str | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @computed_field
    @property
    def total_cost(self) -> Decimal:
        return (self.price_per_person * Decimal(self.travellers)).quantize(Decimal("0.01"))


class BudgetBreakdown(BaseModel):
    """Verified trip expense calculation."""

    accommodation: Decimal = Field(ge=0)
    intercity_transport: Decimal = Field(ge=0)
    local_transport: Decimal = Field(ge=0)
    attractions: Decimal = Field(ge=0)
    food: Decimal = Field(ge=0)
    shopping: Decimal = Field(default=Decimal("0.00"), ge=0)
    miscellaneous: Decimal = Field(default=Decimal("0.00"), ge=0)
    contingency_percentage: Decimal = Field(default=Decimal("5.00"), ge=0, le=50)
    customer_budget: Decimal = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return sum(
            (
                self.accommodation,
                self.intercity_transport,
                self.local_transport,
                self.attractions,
                self.food,
                self.shopping,
                self.miscellaneous,
            ),
            Decimal("0.00"),
        ).quantize(Decimal("0.01"))

    @computed_field
    @property
    def contingency_amount(self) -> Decimal:
        return (self.subtotal * self.contingency_percentage / Decimal("100")).quantize(
            Decimal("0.01")
        )

    @computed_field
    @property
    def estimated_total(self) -> Decimal:
        return (self.subtotal + self.contingency_amount).quantize(Decimal("0.01"))

    @computed_field
    @property
    def difference(self) -> Decimal:
        return (self.customer_budget - self.estimated_total).quantize(Decimal("0.01"))

    @computed_field
    @property
    def within_budget(self) -> bool:
        return self.estimated_total <= self.customer_budget

    @computed_field
    @property
    def status(self) -> str:
        return "within_budget" if self.within_budget else "over_budget"
