from decimal import Decimal

from smart_travel_planner.models.travel_options import DataMode
from smart_travel_planner.providers import MockTravelProvider


def test_mock_hotel_provider_calculates_rooms_and_total() -> None:
    provider = MockTravelProvider()

    options = provider.find_hotels(
        destination="Jaipur",
        nights=4,
        travellers=3,
        preference="budget",
    )

    assert len(options) == 2
    assert options[0].rooms == 2
    assert options[0].nights == 4
    assert options[0].total_cost == Decimal("17600.00")
    assert options[0].data_mode == DataMode.MOCK


def test_mock_transport_returns_preferred_mode_first() -> None:
    provider = MockTravelProvider()

    options = provider.find_transport(
        origin="Mumbai",
        destination="Jaipur",
        travellers=2,
        preferred_mode="train",
    )

    assert len(options) == 3
    assert options[0].mode == "train"
    assert options[0].total_cost == Decimal("5600.00")
    assert all(option.data_mode == DataMode.MOCK for option in options)
