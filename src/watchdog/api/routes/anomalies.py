from fastapi import APIRouter, Query
from sqlalchemy import func, select

from watchdog.api.deps import DbSession
from watchdog.models.document import Anomaly

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("")
async def list_anomalies(
    db: DbSession,
    severity: str | None = None,
    anomaly_type: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    query = select(Anomaly).offset(offset).limit(limit).order_by(Anomaly.confidence.desc())
    if severity:
        query = query.where(Anomaly.severity == severity)
    if anomaly_type:
        query = query.where(Anomaly.anomaly_type == anomaly_type)

    result = await db.execute(query)
    anomalies = result.scalars().all()

    count_query = select(func.count(Anomaly.id))
    if severity:
        count_query = count_query.where(Anomaly.severity == severity)
    if anomaly_type:
        count_query = count_query.where(Anomaly.anomaly_type == anomaly_type)
    total = (await db.execute(count_query)).scalar()

    return {
        "total": total,
        "anomalies": [
            {
                "id": a.id,
                "document_id": a.document_id,
                "anomaly_type": a.anomaly_type,
                "description": a.description,
                "severity": a.severity,
                "confidence": a.confidence,
                "evidence": a.evidence,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in anomalies
        ],
    }
