"""Frontend-only view models and formatting helpers."""

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class TripFormData(BaseModel):
    """Values collected from the Streamlit travel form."""

    starting_location: str
    destination: str
    start_date: date
    end_date: date
    travellers: int = Field(ge=1, le=20)
    total_budget: Decimal = Field(gt=0)
    currency: str
    interests: list[str] = Field(min_length=1)
    accommodation_preference: str
    transport_preference: str
    special_requirements: str | None = None


def format_currency(
    value: Decimal | float | int | str,
    currency: str = "INR",
) -> str:
    """Format a monetary value for dashboard display."""

    amount = Decimal(str(value))

    symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "AED": "AED ",
    }

    symbol = symbols.get(currency.upper(), f"{currency.upper()} ")

    return f"{symbol}{amount:,.2f}"


def safe_text(value: Any, fallback: str = "Not available") -> str:
    """Return display-safe text for optional values."""

    if value is None:
        return fallback

    rendered = str(value).strip()
    return rendered or fallback
