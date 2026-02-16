from fastapi import APIRouter
from sqlalchemy import func, select

from watchdog.api.deps import DbSession
from watchdog.models.document import Anomaly, Chunk, Document, Entity, Expense

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(db: DbSession):
    doc_count = (await db.execute(select(func.count(Document.id)))).scalar()
    chunk_count = (await db.execute(select(func.count(Chunk.id)))).scalar()
    entity_count = (await db.execute(select(func.count(Entity.id)))).scalar()
    anomaly_count = (await db.execute(select(func.count(Anomaly.id)))).scalar()

    # Status breakdown
    status_result = await db.execute(
        select(Document.status, func.count(Document.id)).group_by(Document.status)
    )
    status_breakdown = {row[0]: row[1] for row in status_result.all()}

    # Cost
    total_cost = (await db.execute(select(func.sum(Expense.cost_usd)))).scalar() or 0.0
    total_input = (await db.execute(select(func.sum(Expense.input_tokens)))).scalar() or 0
    total_output = (await db.execute(select(func.sum(Expense.output_tokens)))).scalar() or 0

    # Top entities
    top_entities_result = await db.execute(
        select(Entity.name, Entity.entity_type, Entity.mention_count)
        .order_by(Entity.mention_count.desc())
        .limit(20)
    )
    top_entities = [
        {"name": r[0], "type": r[1], "mentions": r[2]}
        for r in top_entities_result.all()
    ]

    # Severity breakdown
    severity_result = await db.execute(
        select(Anomaly.severity, func.count(Anomaly.id)).group_by(Anomaly.severity)
    )
    severity_breakdown = {row[0]: row[1] for row in severity_result.all()}

    return {
        "documents": doc_count,
        "chunks": chunk_count,
        "entities": entity_count,
        "anomalies": anomaly_count,
        "status_breakdown": status_breakdown,
        "cost": {
            "total_usd": round(float(total_cost), 4),
            "input_tokens": int(total_input),
            "output_tokens": int(total_output),
        },
        "top_entities": top_entities,
        "anomaly_severity": severity_breakdown,
    }
