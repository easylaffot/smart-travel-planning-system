from contextlib import nullcontext

from frontend import result_components


def test_destination_helpers_format_categories_and_data_labels() -> None:
    assert result_components._format_category("local_food") == "Local Food"
    assert result_components._format_category("cultural_experience") == "Cultural Experience"
    assert result_components._data_mode_label("live") == "Live Source"
    assert result_components._data_mode_label("mock") == "Mock Fallback"
    assert result_components._data_mode_label("unavailable") == "Unavailable"


def test_source_url_requires_http_scheme() -> None:
    assert result_components._safe_source_url("https://example.com/source") == (
        "https://example.com/source"
    )
    assert result_components._safe_source_url("http://example.com/source") == (
        "http://example.com/source"
    )
    assert result_components._safe_source_url("javascript:alert(1)") is None
    assert result_components._safe_source_url("/relative/source") is None


def test_option_card_uses_single_streamlit_container_and_safe_source(monkeypatch) -> None:
    markdown_calls = []
    links = []
    monkeypatch.setattr(result_components.st, "container", lambda **kwargs: nullcontext())
    monkeypatch.setattr(
        result_components.st,
        "markdown",
        lambda value, **kwargs: markdown_calls.append(value),
    )
    monkeypatch.setattr(
        result_components.st,
        "link_button",
        lambda label, url: links.append((label, url)),
    )
    monkeypatch.setattr(
        result_components.st,
        "columns",
        lambda _: [
            _Column(),
            _Column(),
        ],
    )
    monkeypatch.setattr(result_components, "render_status_badge", lambda *args: None)

    result_components.render_option_card(
        title="Prototype attraction",
        lines=[("Category", "Local Food")],
        data_mode="mock",
        source_url="file:///untrusted",
    )

    assert not any("<div" in str(call) or "</div>" in str(call) for call in markdown_calls)
    assert links == []


def test_hotel_and_transport_amounts_are_explicitly_estimated(monkeypatch) -> None:
    rendered_cards = []
    monkeypatch.setattr(result_components.st, "columns", lambda _: [_Column(), _Column()])
    monkeypatch.setattr(
        result_components,
        "render_option_card",
        lambda **kwargs: rendered_cards.append(kwargs),
    )

    result_components.render_options(
        [{"name": "Prototype hotel", "total_cost": "100.00"}],
        option_type="hotel",
        currency="INR",
    )
    result_components.render_options(
        [{"operator": "Prototype carrier", "total_cost": "200.00"}],
        option_type="transport",
        currency="INR",
    )

    assert "Estimated Price" in dict(rendered_cards[0]["lines"])
    assert "Estimated Fare" in dict(rendered_cards[1]["lines"])


class _Column:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def caption(self, value):
        pass

    def markdown(self, value):
        pass
