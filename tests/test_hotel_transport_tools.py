import json

from smart_travel_planner.tools import (
    HotelSearchTool,
    TransportSearchTool,
)


def test_hotel_tool_returns_structured_mock_results() -> None:
    tool = HotelSearchTool()

    raw_result = tool._run(
        destination="Jaipur",
        nights=4,
        travellers=2,
        preference="mid_range",
    )
    result = json.loads(raw_result)

    assert result["status"] == "success"
    assert result["data_mode"] == "mock"
    assert len(result["options"]) == 2
    assert result["options"][0]["total_cost"] == "16800.00"


def test_transport_tool_returns_preferred_mode_first() -> None:
    tool = TransportSearchTool()

    raw_result = tool._run(
        origin="Mumbai",
        destination="Jaipur",
        travellers=2,
        preferred_mode="flight",
    )
    result = json.loads(raw_result)

    assert result["status"] == "success"
    assert result["data_mode"] == "mock"
    assert result["options"][0]["mode"] == "flight"
    assert result["options"][0]["total_cost"] == "15600.00"
