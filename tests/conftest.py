from datetime import date, timedelta
from decimal import Decimal

import pytest

from smart_travel_planner.models import Activity


@pytest.fixture
def valid_request_data() -> dict:
    start = date.today() + timedelta(days=10)
    return {
        "starting_location": "Mumbai",
        "destination": "Jaipur",
        "start_date": start,
        "end_date": start + timedelta(days=3),
        "travellers": 2,
        "total_budget": Decimal("60000.00"),
        "currency": "inr",
        "interests": [Activity.SIGHTSEEING, Activity.LOCAL_FOOD],
        "transport_preference": "flight",
    }
