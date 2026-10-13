"""Deterministic mock hotel and transport provider.

This provider is used for development, automated tests, and as a clearly
labelled fallback when a permitted live booking API is unavailable.
"""

from decimal import Decimal
from math import ceil

from smart_travel_planner.models.travel_options import (
    DataMode,
    HotelOption,
    TransportOption,
)


class MockTravelProvider:
    """Return repeatable mock travel inventory."""

    HOTEL_RATES = {
        "budget": (
            ("City Comfort Inn", Decimal("2200.00"), Decimal("3.7")),
            ("Traveller Residency", Decimal("2800.00"), Decimal("4.0")),
        ),
        "mid_range": (
            ("Central Park Hotel", Decimal("4200.00"), Decimal("4.2")),
            ("Heritage Grand Stay", Decimal("5200.00"), Decimal("4.4")),
        ),
        "premium": (
            ("Royal Horizon Hotel", Decimal("8500.00"), Decimal("4.7")),
            ("The Imperial Retreat", Decimal("11000.00"), Decimal("4.9")),
        ),
    }

    TRANSPORT_RATES = {
        "flight": (
            "SkyConnect Airways",
            Decimal("7800.00"),
            130,
            "08:30",
            "10:40",
        ),
        "train": (
            "National Rail Express",
            Decimal("2800.00"),
            960,
            "17:30",
            "09:30",
        ),
        "bus": (
            "InterCity Coach",
            Decimal("1900.00"),
            1020,
            "18:00",
            "11:00",
        ),
    }

    def find_hotels(
        self,
        destination: str,
        nights: int,
        travellers: int,
        preference: str = "mid_range",
        currency: str = "INR",
    ) -> list[HotelOption]:
        """Return matching the requested category."""

        if nights < 1:
            raise ValueError("nights must be at least 1")

        if travellers < 1:
            raise ValueError("travellers must be at least 1")

        normalized_preference = preference.strip().lower().replace("-", "_")

        if normalized_preference not in self.HOTEL_RATES:
            normalized_preference = "mid_range"

        rooms = ceil(travellers / 2)
        options: list[HotelOption] = []

        for index, (name, rate, rating) in enumerate(
            self.HOTEL_RATES[normalized_preference],
            start=1,
        ):
            options.append(
                HotelOption(
                    hotel_id=(f"MOCK-HOTEL-{normalized_preference.upper()}-{index}"),
                    name=name,
                    destination=destination.strip(),
                    category=normalized_preference,
                    price_per_room_per_night=rate,
                    rooms=rooms,
                    nights=nights,
                    currency=currency,
                    rating=rating,
                    amenities=[
                        "Wi-Fi",
                        "Breakfast",
                        "24-hour reception",
                    ],
                    data_mode=DataMode.MOCK,
                    provider="mock_hotel_provider",
                )
            )

        return options

    def find_transport(
        self,
        origin: str,
        destination: str,
        travellers: int,
        preferred_mode: str = "flight",
        currency: str = "INR",
    ) -> list[TransportOption]:
        """Return preferred and alternative mock transport options."""

        if travellers < 1:
            raise ValueError("travellers must be at least 1")

        normalized_mode = preferred_mode.strip().lower()

        ordered_modes = [
            normalized_mode,
            "flight",
            "train",
            "bus",
        ]

        unique_modes = list(dict.fromkeys(ordered_modes))

        valid_modes = [mode for mode in unique_modes if mode in self.TRANSPORT_RATES]

        options: list[TransportOption] = []

        for index, mode in enumerate(valid_modes, start=1):
            (
                operator,
                price,
                duration,
                departure,
                arrival,
            ) = self.TRANSPORT_RATES[mode]

            options.append(
                TransportOption(
                    transport_id=(f"MOCK-TRANSPORT-{mode.upper()}-{index}"),
                    mode=mode,
                    operator=operator,
                    origin=origin.strip(),
                    destination=destination.strip(),
                    departure_time=departure,
                    arrival_time=arrival,
                    duration_minutes=duration,
                    price_per_person=price,
                    travellers=travellers,
                    currency=currency,
                    data_mode=DataMode.MOCK,
                    provider="mock_transport_provider",
                )
            )

        return options
