"""Accessibility checks for Streamlit form widgets."""

from streamlit.testing.v1 import AppTest


def _render_trip_form() -> None:
    from unittest.mock import patch

    from frontend.app import render_trip_form
    from frontend.saved_plans import render_saved_plan_lookup

    class Repository:
        def list_application_ids(self) -> list[str]:
            return ["TRIP-TEST"]

    render_trip_form()
    with patch(
        "frontend.saved_plans.get_repository",
        return_value=Repository(),
    ):
        render_saved_plan_lookup()


def test_trip_location_fields_use_city_autocomplete() -> None:
    app = AppTest.from_function(_render_trip_form).run(timeout=30)

    assert not app.exception
    location_fields = {widget.label: widget for widget in app.text_input}

    assert location_fields["Starting location"].value == "Mumbai"
    assert location_fields["Destination"].value == "Jaipur"
    assert location_fields["Starting location"].proto.autocomplete == "address-level2"
    assert location_fields["Destination"].proto.autocomplete == "address-level2"
    assert location_fields["Or enter an application ID"].proto.autocomplete == "off"
