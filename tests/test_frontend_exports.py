"""Tests for frontend exports and saved-plan retrieval."""

import json

from frontend.exporters import (
    build_json_export,
    build_markdown_export,
    safe_download_filename,
)
from smart_travel_planner.models import (
    PlanningResult,
    WorkflowStatus,
)
from smart_travel_planner.storage import PlanRepository
from tests.phase4_fixtures import (
    make_customer_request,
    make_final_plan,
)


def make_result() -> PlanningResult:
    """Create one exportable planning result."""

    return PlanningResult(
        application_id="TRIP-EXPORT0001",
        status=WorkflowStatus.COMPLETED_WITHIN_BUDGET,
        customer_request=make_customer_request(),
        travel_plan=make_final_plan(within_budget=True),
        warnings=["Prototype mock data is present."],
    )


def test_json_export_contains_application_and_plan() -> None:
    """JSON export should preserve structured travel data."""

    result = make_result()
    payload = json.loads(build_json_export(result))

    assert payload["application_id"] == result.application_id
    assert payload["status"] == result.status.value
    assert payload["travel_plan"] is not None


def test_markdown_export_contains_core_sections() -> None:
    """Markdown export should contain important plan sections."""

    markdown = build_markdown_export(make_result())

    assert "# Smart Travel Plan" in markdown
    assert "## Trip Overview" in markdown
    assert "## Budget Summary" in markdown
    assert "## Day-by-Day Itinerary" in markdown
    assert "## Warnings and Limitations" in markdown


def test_download_filename_is_sanitized() -> None:
    """Unsafe filename characters should be removed."""

    filename = safe_download_filename(
        "TRIP/ABC:123",
        ".json",
    )

    assert filename == "TRIPABC123.json"


def test_repository_supports_frontend_plan_retrieval(
    tmp_path,
) -> None:
    """Saved plans should round-trip through SQLite."""

    repository = PlanRepository(tmp_path / "plans.db")
    result = make_result()

    repository.save(result)
    loaded = repository.get(result.application_id)

    assert loaded is not None
    assert loaded.application_id == result.application_id
    assert loaded.travel_plan == result.travel_plan
