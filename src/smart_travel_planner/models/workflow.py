"""Models used by the integrated travel-planning workflow."""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from smart_travel_planner.models.agent_outputs import FinalTravelPlanOutput
from smart_travel_planner.models.customer_request import CustomerTravelRequest


class WorkflowStatus(StrEnum):
    """Supported travel-workflow completion states."""

    COMPLETED_WITHIN_BUDGET = "completed_within_budget"
    COMPLETED_AFTER_REVISION = "completed_after_revision"
    COMPLETED_OVER_BUDGET = "completed_over_budget"
    EXECUTION_FAILED = "execution_failed"
    VALIDATION_FAILED = "validation_failed"


class RevisionRecord(BaseModel):
    """One deterministic budget-revision attempt."""

    revision_number: int = Field(ge=1)
    original_total: Decimal = Field(ge=0)
    revised_total: Decimal = Field(ge=0)
    savings_achieved: Decimal = Field(ge=0)
    original_hotel_cost: Decimal = Field(ge=0)
    revised_hotel_cost: Decimal = Field(ge=0)
    original_transport_cost: Decimal = Field(ge=0)
    revised_transport_cost: Decimal = Field(ge=0)
    remaining_difference: Decimal
    selected_hotel: str | None = None
    selected_transport: str | None = None
    reason: str


class RevisionOutcome(BaseModel):
    """Result returned by deterministic budget optimization."""

    travel_plan: FinalTravelPlanOutput
    revisions: list[RevisionRecord] = Field(default_factory=list)
    exhausted: bool = False

    @property
    def revision_count(self):
        """Return the number of applied revisions."""

        return len(self.revisions)


class CrewExecutionResult(BaseModel):
    """Normalized result returned by a crew runner."""

    raw_output: str | None = None
    structured_output: FinalTravelPlanOutput | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlanningResult(BaseModel):
    """Application-level result returned by the planning service."""

    application_id: str = Field(default_factory=lambda: f"TRIP-{uuid4().hex[:12].upper()}")
    status: WorkflowStatus
    customer_request: CustomerTravelRequest
    travel_plan: FinalTravelPlanOutput | None = None
    revision_count: int = Field(default=0, ge=0)
    revisions: list[RevisionRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
