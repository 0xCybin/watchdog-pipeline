import structlog
from sqlalchemy import func, select

from watchdog.database import async_session_factory
from watchdog.models.document import Expense

log = structlog.get_logger()

# Pricing per 1M tokens (as of early 2026)
PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for a Claude API call."""
    prices = PRICING.get(model, {"input": 3.00, "output": 15.00})
    cost = (input_tokens / 1_000_000) * prices["input"] + (output_tokens / 1_000_000) * prices["output"]
    return round(cost, 6)


async def track_expense(
    model: str,
    operation: str,
    input_tokens: int,
    output_tokens: int,
    document_id: str | None = None,
) -> Expense:
    """Log an API expense to the database."""
    cost = calculate_cost(model, input_tokens, output_tokens)

    async with async_session_factory() as session:
        expense = Expense(
            service="anthropic",
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            document_id=document_id,
        )
        session.add(expense)
        await session.commit()

    log.info(
        "expense_tracked",
        operation=operation,
        cost_usd=cost,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    return expense


async def get_total_cost() -> dict:
    """Get total cost breakdown."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(
                Expense.operation,
                func.sum(Expense.cost_usd).label("total_cost"),
                func.sum(Expense.input_tokens).label("total_input"),
                func.sum(Expense.output_tokens).label("total_output"),
                func.count(Expense.id).label("call_count"),
            ).group_by(Expense.operation)
        )
        rows = result.all()

        breakdown = {}
        total = 0.0
        for row in rows:
            breakdown[row.operation] = {
                "cost_usd": round(float(row.total_cost), 4),
                "input_tokens": int(row.total_input),
                "output_tokens": int(row.total_output),
                "calls": int(row.call_count),
            }
            total += float(row.total_cost)

        return {"total_usd": round(total, 4), "breakdown": breakdown}
