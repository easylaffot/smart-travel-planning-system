from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from smart_travel_planner.models import CustomerTravelRequest


def test_valid_request_is_normalized(valid_request_data: dict) -> None:
    request = CustomerTravelRequest(**valid_request_data)
    assert request.currency == "INR"
    assert request.duration_days == 4
    assert request.starting_location == "Mumbai"


def test_end_date_before_start_date_is_rejected(valid_request_data: dict) -> None:
    valid_request_data["end_date"] = valid_request_data["start_date"] - timedelta(days=1)
    with pytest.raises(ValidationError, match="end_date cannot be before start_date"):
        CustomerTravelRequest(**valid_request_data)


def test_past_start_date_is_rejected(valid_request_data: dict) -> None:
    valid_request_data["start_date"] = date.today() - timedelta(days=1)
    valid_request_data["end_date"] = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError, match="start_date cannot be in the past"):
        CustomerTravelRequest(**valid_request_data)


def test_same_origin_and_destination_is_rejected(valid_request_data: dict) -> None:
    valid_request_data["destination"] = " mumbai "
    with pytest.raises(ValidationError, match="destination must differ"):
        CustomerTravelRequest(**valid_request_data)


def test_interest_list_is_required(valid_request_data: dict) -> None:
    valid_request_data["interests"] = []
    with pytest.raises(ValidationError):
        CustomerTravelRequest(**valid_request_data)
