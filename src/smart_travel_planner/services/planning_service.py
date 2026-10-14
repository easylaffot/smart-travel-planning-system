"""Application service for controlled travel planning and revision."""

from smart_travel_planner.models import (
    CustomerTravelRequest,
    PlanningResult,
    WorkflowStatus,
)
from smart_travel_planner.services.crew_runner import CrewRunner
from smart_travel_planner.services.input_builder import (
    KickoffInputBuilder,
)
from smart_travel_planner.services.result_parser import (
    TravelPlanResultParser,
)
from smart_travel_planner.services.revision_service import (
    BudgetRevisionService,
)
from smart_travel_planner.utils.exceptions import (
    AgentExecutionError,
    ResultParsingError,
)


class TravelPlanningService:
    """Execute one crew run and apply controlled budget revision."""

    def __init__(
        self,
        runner: CrewRunner,
        input_builder=None,
        result_parser=None,
        revision_service=None,
    ):
        self.runner = runner
        self.input_builder = input_builder or KickoffInputBuilder()
        self.result_parser = result_parser or TravelPlanResultParser()
        self.revision_service = revision_service or BudgetRevisionService()

    def create_plan(self, request: CustomerTravelRequest):
        """Create and revise one travel plan when required."""

        kickoff_inputs = self.input_builder.build(request)

        try:
            execution_result = self.runner.run(kickoff_inputs)
            travel_plan = self.result_parser.parse(execution_result)
        except AgentExecutionError as exc:
            return PlanningResult(
                status=WorkflowStatus.EXECUTION_FAILED,
                customer_request=request,
                errors=[str(exc)],
            )
        except ResultParsingError as exc:
            return PlanningResult(
                status=WorkflowStatus.VALIDATION_FAILED,
                customer_request=request,
                errors=[str(exc)],
            )

        if travel_plan.budget_analysis.within_budget:
            return PlanningResult(
                status=WorkflowStatus.COMPLETED_WITHIN_BUDGET,
                customer_request=request,
                travel_plan=travel_plan,
                warnings=list(travel_plan.validation_warnings),
            )

        outcome = self.revision_service.revise(
            request=request,
            travel_plan=travel_plan,
        )

        if outcome.travel_plan.budget_analysis.within_budget:
            status = WorkflowStatus.COMPLETED_AFTER_REVISION
        else:
            status = WorkflowStatus.COMPLETED_OVER_BUDGET

        warnings = list(outcome.travel_plan.validation_warnings)

        if status == WorkflowStatus.COMPLETED_OVER_BUDGET:
            warnings.append("The plan remains over budget after available deterministic revisions.")

        return PlanningResult(
            status=status,
            customer_request=request,
            travel_plan=outcome.travel_plan,
            revision_count=outcome.revision_count,
            revisions=outcome.revisions,
            warnings=warnings,
        )
