"""Deterministic CrewAI budget-calculation tool."""

from decimal import Decimal, InvalidOperation

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, field_validator

from smart_travel_planner.models.travel_options import BudgetBreakdown


class BudgetCalculatorInput(BaseModel):
    """Validated expense values supplied to the calculator."""

    accommodation: Decimal = Field(ge=0)
    intercity_transport: Decimal = Field(ge=0)
    local_transport: Decimal = Field(ge=0)
    attractions: Decimal = Field(ge=0)
    food: Decimal = Field(ge=0)
    shopping: Decimal = Field(default=Decimal("0.00"), ge=0)
    miscellaneous: Decimal = Field(default=Decimal("0.00"), ge=0)
    contingency_percentage: Decimal = Field(
        default=Decimal("5.00"),
        ge=0,
        le=50,
    )
    customer_budget: Decimal = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator(
        "accommodation",
        "intercity_transport",
        "local_transport",
        "attractions",
        "food",
        "shopping",
        "miscellaneous",
        "contingency_percentage",
        "customer_budget",
        mode="before",
    )
    @classmethod
    def reject_invalid_numbers(cls, value: object) -> Decimal:
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("expense values must be valid numbers") from exc

        if not parsed.is_finite():
            raise ValueError("expense values must be finite")

        return parsed


class BudgetCalculatorTool(BaseTool):
    """Calculate and compare travel costs without LLM arithmetic."""

    name: str = "travel_budget_calculator"
    description: str = (
        "Calculate verified trip expenses, contingency, total cost, "
        "budget difference, and whether the plan is within budget. "
        "Always use this tool for final arithmetic."
    )
    args_schema: type[BaseModel] = BudgetCalculatorInput

    def _run(
        self,
        accommodation: Decimal,
        intercity_transport: Decimal,
        local_transport: Decimal,
        attractions: Decimal,
        food: Decimal,
        customer_budget: Decimal,
        shopping: Decimal = Decimal("0.00"),
        miscellaneous: Decimal = Decimal("0.00"),
        contingency_percentage: Decimal = Decimal("5.00"),
        currency: str = "INR",
    ) -> str:
        breakdown = BudgetBreakdown(
            accommodation=accommodation,
            intercity_transport=intercity_transport,
            local_transport=local_transport,
            attractions=attractions,
            food=food,
            shopping=shopping,
            miscellaneous=miscellaneous,
            contingency_percentage=contingency_percentage,
            customer_budget=customer_budget,
            currency=currency,
        )

        return breakdown.model_dump_json(indent=2)
