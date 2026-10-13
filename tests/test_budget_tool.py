import json
from decimal import Decimal

from smart_travel_planner.models.travel_options import BudgetBreakdown
from smart_travel_planner.tools import BudgetCalculatorTool


def test_budget_breakdown_within_budget() -> None:
    budget = BudgetBreakdown(
        accommodation=Decimal("16800"),
        intercity_transport=Decimal("15600"),
        local_transport=Decimal("4000"),
        attractions=Decimal("5000"),
        food=Decimal("8000"),
        shopping=Decimal("2000"),
        miscellaneous=Decimal("1000"),
        contingency_percentage=Decimal("5"),
        customer_budget=Decimal("60000"),
    )

    assert budget.subtotal == Decimal("52400.00")
    assert budget.contingency_amount == Decimal("2620.00")
    assert budget.estimated_total == Decimal("55020.00")
    assert budget.difference == Decimal("4980.00")
    assert budget.within_budget is True
    assert budget.status == "within_budget"


def test_budget_tool_detects_over_budget_plan() -> None:
    tool = BudgetCalculatorTool()

    raw_result = tool._run(
        accommodation=Decimal("30000"),
        intercity_transport=Decimal("20000"),
        local_transport=Decimal("5000"),
        attractions=Decimal("6000"),
        food=Decimal("10000"),
        shopping=Decimal("2000"),
        miscellaneous=Decimal("1000"),
        contingency_percentage=Decimal("5"),
        customer_budget=Decimal("60000"),
    )
    result = json.loads(raw_result)

    assert result["subtotal"] == "74000.00"
    assert result["contingency_amount"] == "3700.00"
    assert result["estimated_total"] == "77700.00"
    assert result["difference"] == "-17700.00"
    assert result["within_budget"] is False
    assert result["status"] == "over_budget"
