from pydantic import BaseModel, Field
from fastapi import APIRouter

from watchdog.api.deps import DbSession
from watchdog.services.embedding import search_similar

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, le=50)


@router.post("")
async def semantic_search(request: SearchRequest, db: DbSession):
    results = await search_similar(request.query, db, limit=request.limit)
    return {"query": request.query, "results": results, "count": len(results)}
