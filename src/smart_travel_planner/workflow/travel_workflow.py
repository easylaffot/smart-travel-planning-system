"""End-to-end controlled travel-planning workflow."""

from smart_travel_planner.models import (
    CustomerTravelRequest,
    PlanningResult,
    WorkflowStatus,
)
from smart_travel_planner.services import TravelPlanningService
from smart_travel_planner.services.plan_validator import (
    FinalPlanValidator,
)
from smart_travel_planner.storage import PlanRepository
from smart_travel_planner.utils.exceptions import PlanValidationError


class TravelPlanningWorkflow:
    """Execute, validate, and optionally persist one travel plan."""

    def __init__(
        self,
        planning_service: TravelPlanningService,
        validator: FinalPlanValidator | None = None,
        repository: PlanRepository | None = None,
    ) -> None:
        self.planning_service = planning_service
        self.validator = validator or FinalPlanValidator()
        self.repository = repository

    def run(
        self,
        request: CustomerTravelRequest,
    ) -> PlanningResult:
        """Run the controlled planning workflow."""

        result = self.planning_service.create_plan(request)

        if result.travel_plan is not None:
            try:
                validation_warnings = self.validator.validate(
                    request=request,
                    plan=result.travel_plan,
                )
                result.warnings.extend(validation_warnings)
                result.warnings = list(dict.fromkeys(result.warnings))
            except PlanValidationError as exc:
                result.status = WorkflowStatus.VALIDATION_FAILED
                result.errors.append(str(exc))
                result.travel_plan.approved = False

        if self.repository is not None:
            self.repository.save(result)

        return result
