"""Tests for SQLite travel-plan persistence."""

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
    return PlanningResult(
        application_id="TRIP-TEST000001",
        status=WorkflowStatus.COMPLETED_WITHIN_BUDGET,
        customer_request=make_customer_request(),
        travel_plan=make_final_plan(within_budget=True),
    )


def test_repository_saves_and_retrieves_plan(tmp_path) -> None:
    repository = PlanRepository(tmp_path / "travel_plans.db")
    result = make_result()

    repository.save(result)
    loaded = repository.get(result.application_id)

    assert loaded is not None
    assert loaded.application_id == result.application_id
    assert loaded.status == result.status
    assert loaded.travel_plan == result.travel_plan


def test_repository_returns_none_for_unknown_id(tmp_path) -> None:
    repository = PlanRepository(tmp_path / "travel_plans.db")

    assert repository.get("TRIP-NOT-FOUND") is None


def test_repository_replaces_existing_application(tmp_path) -> None:
    repository = PlanRepository(tmp_path / "travel_plans.db")
    result = make_result()

    repository.save(result)

    result.status = WorkflowStatus.COMPLETED_AFTER_REVISION
    repository.save(result)

    loaded = repository.get(result.application_id)

    assert loaded is not None
    assert loaded.status == WorkflowStatus.COMPLETED_AFTER_REVISION


def test_repository_lists_application_ids(tmp_path) -> None:
    repository = PlanRepository(tmp_path / "travel_plans.db")
    result = make_result()

    repository.save(result)

    assert repository.list_application_ids() == [result.application_id]
