"""Offline end-to-end workflow tests."""

from smart_travel_planner.models import WorkflowStatus
from smart_travel_planner.services import (
    FakeCrewRunner,
    TravelPlanningService,
)
from smart_travel_planner.storage import PlanRepository
from smart_travel_planner.workflow import TravelPlanningWorkflow
from tests.phase4_fixtures import (
    make_customer_request,
    make_execution_result,
)


def test_workflow_validates_and_persists_plan(tmp_path) -> None:
    request = make_customer_request()
    runner = FakeCrewRunner(make_execution_result(within_budget=True))

    repository = PlanRepository(tmp_path / "plans.db")

    workflow = TravelPlanningWorkflow(
        planning_service=TravelPlanningService(runner),
        repository=repository,
    )

    result = workflow.run(request)
    stored = repository.get(result.application_id)

    assert result.status == WorkflowStatus.COMPLETED_WITHIN_BUDGET
    assert stored is not None
    assert stored.application_id == result.application_id
    assert runner.call_count == 1


def test_workflow_preserves_mock_data_warning(tmp_path) -> None:
    request = make_customer_request()

    workflow = TravelPlanningWorkflow(
        planning_service=TravelPlanningService(
            FakeCrewRunner(make_execution_result(within_budget=True))
        ),
        repository=PlanRepository(tmp_path / "plans.db"),
    )

    result = workflow.run(request)

    assert any("mock data" in warning for warning in result.warnings)


def test_workflow_marks_invalid_plan_as_validation_failed(
    tmp_path,
) -> None:
    request = make_customer_request()
    execution = make_execution_result(within_budget=True)

    assert execution.structured_output is not None
    execution.structured_output.itinerary.destination = "Udaipur"

    repository = PlanRepository(tmp_path / "plans.db")

    workflow = TravelPlanningWorkflow(
        planning_service=TravelPlanningService(FakeCrewRunner(execution)),
        repository=repository,
    )

    result = workflow.run(request)
    stored = repository.get(result.application_id)

    assert result.status == WorkflowStatus.VALIDATION_FAILED
    assert result.errors
    assert stored is not None
    assert stored.status == WorkflowStatus.VALIDATION_FAILED
