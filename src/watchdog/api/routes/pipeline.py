from fastapi import APIRouter
from sqlalchemy import func, select

from watchdog.api.deps import DbSession
from watchdog.models.document import Document, ProcessingJob

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/status")
async def pipeline_status(db: DbSession):
    # Document status counts
    status_result = await db.execute(
        select(Document.status, func.count(Document.id)).group_by(Document.status)
    )
    statuses = {row[0]: row[1] for row in status_result.all()}

    # Recent jobs
    jobs_result = await db.execute(
        select(ProcessingJob)
        .order_by(ProcessingJob.created_at.desc())
        .limit(20)
    )
    jobs = jobs_result.scalars().all()

    total_docs = sum(statuses.values())
    triaged = statuses.get("triaged", 0)

    return {
        "total_documents": total_docs,
        "document_statuses": statuses,
        "progress_pct": round((triaged / total_docs * 100) if total_docs > 0 else 0, 1),
        "recent_jobs": [
            {
                "id": j.id,
                "job_type": j.job_type,
                "status": j.status,
                "document_id": j.document_id,
                "error_message": j.error_message,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in jobs
        ],
    }
