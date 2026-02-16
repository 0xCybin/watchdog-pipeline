from fastapi import APIRouter, Query
from sqlalchemy import func, select

from watchdog.api.deps import DbSession
from watchdog.models.document import Entity, EntityMention, EntityRelationship

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("")
async def list_entities(
    db: DbSession,
    entity_type: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    query = select(Entity).offset(offset).limit(limit).order_by(Entity.mention_count.desc())
    if entity_type:
        query = query.where(Entity.entity_type == entity_type)

    result = await db.execute(query)
    entities = result.scalars().all()

    count_query = select(func.count(Entity.id))
    if entity_type:
        count_query = count_query.where(Entity.entity_type == entity_type)
    total = (await db.execute(count_query)).scalar()

    return {
        "total": total,
        "entities": [
            {
                "id": e.id,
                "name": e.name,
                "entity_type": e.entity_type,
                "description": e.description,
                "mention_count": e.mention_count,
            }
            for e in entities
        ],
    }


@router.get("/{entity_id}")
async def get_entity(entity_id: str, db: DbSession):
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Entity not found")

    # Get mentions
    mentions_result = await db.execute(
        select(EntityMention).where(EntityMention.entity_id == entity_id).limit(50)
    )
    mentions = mentions_result.scalars().all()

    # Get relationships
    rels_result = await db.execute(
        select(EntityRelationship).where(
            (EntityRelationship.source_entity_id == entity_id)
            | (EntityRelationship.target_entity_id == entity_id)
        ).limit(50)
    )
    relationships = rels_result.scalars().all()

    return {
        "id": entity.id,
        "name": entity.name,
        "entity_type": entity.entity_type,
        "description": entity.description,
        "mention_count": entity.mention_count,
        "mentions": [
            {
                "id": m.id,
                "chunk_id": m.chunk_id,
                "context_snippet": m.context_snippet,
            }
            for m in mentions
        ],
        "relationships": [
            {
                "id": r.id,
                "source_entity_id": r.source_entity_id,
                "target_entity_id": r.target_entity_id,
                "relationship_type": r.relationship_type,
                "description": r.description,
                "confidence": r.confidence,
            }
            for r in relationships
        ],
    }
