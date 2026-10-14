"""Offline verification for the complete Phase 4 workflow."""

import sys

from smart_travel_planner.services import (
    FakeCrewRunner,
    TravelPlanningService,
)
from smart_travel_planner.workflow import TravelPlanningWorkflow
from tests.phase4_fixtures import (
    make_customer_request,
    make_execution_result,
)


def main() -> int:
    """Run the workflow with deterministic offline data."""

    request = make_customer_request()
    runner = FakeCrewRunner(make_execution_result(within_budget=True))

    workflow = TravelPlanningWorkflow(
        planning_service=TravelPlanningService(runner),
    )

    result = workflow.run(request)

    print(f"[OK] Application ID: {result.application_id}")
    print(f"[OK] Status: {result.status.value}")
    print(f"[OK] Crew runner calls: {runner.call_count}")
    print(f"[OK] Revision count: {result.revision_count}")
    print(f"[OK] Final plan available: {result.travel_plan is not None}")
    print("[OK] Live Ollama call: no")
    print("[OK] External provider call: no")

    if result.travel_plan is None:
        print("[FAILED] No travel plan was produced")
        return 1

    if runner.call_count != 1:
        print("[FAILED] Unexpected fake-runner call count")
        return 1

    print("[PASSED] Phase 4 offline workflow verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
