import asyncio
import json
import re
from pathlib import Path

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from watchdog.config import settings
from watchdog.database import async_session_factory
from watchdog.models.document import (
    Anomaly,
    Chunk,
    Document,
    Entity,
    EntityMention,
    EntityRelationship,
)
from watchdog.services.claude_client import call_claude

log = structlog.get_logger()

_prompt_template: str | None = None


def get_prompt_template() -> str:
    global _prompt_template
    if _prompt_template is None:
        prompt_path = Path(__file__).parent / "prompts" / "triage_analysis.txt"
        _prompt_template = prompt_path.read_text(encoding="utf-8")
    return _prompt_template


async def get_or_create_entity(session: AsyncSession, name: str, entity_type: str, description: str | None = None) -> Entity:
    """Get existing entity or create new one."""
    # Normalize name for matching
    normalized = name.strip().title()
    result = await session.execute(
        select(Entity).where(Entity.name == normalized, Entity.entity_type == entity_type)
    )
    entity = result.scalar_one_or_none()

    if entity:
        entity.mention_count += 1
        return entity

    entity = Entity(
        name=normalized,
        entity_type=entity_type,
        description=description,
        mention_count=1,
    )
    session.add(entity)
    await session.flush()
    return entity


async def triage_chunk(chunk: Chunk, session: AsyncSession) -> dict | None:
    """Run Claude triage analysis on a single chunk."""
    text = chunk.filtered_text or chunk.text
    prompt = get_prompt_template().replace("{chunk_text}", text[:6000])

    try:
        response = await call_claude(
            prompt=prompt,
            operation="triage",
            document_id=chunk.document_id,
            max_tokens=2000,
        )

        # Parse JSON
        json_match = re.search(r"\{[\s\S]*\}", response)
        if not json_match:
            log.warning("triage_no_json", chunk_id=chunk.id)
            return None

        result = json.loads(json_match.group())

        # Process entities
        for entity_data in result.get("entities", []):
            entity = await get_or_create_entity(
                session,
                name=entity_data["name"],
                entity_type=entity_data.get("type", "unknown"),
                description=entity_data.get("context"),
            )
            mention = EntityMention(
                entity_id=entity.id,
                chunk_id=chunk.id,
                context_snippet=entity_data.get("context", "")[:500],
            )
            session.add(mention)

        # Process relationships
        for rel_data in result.get("relationships", []):
            source_entity = await get_or_create_entity(
                session,
                name=rel_data["source"],
                entity_type="unknown",
            )
            target_entity = await get_or_create_entity(
                session,
                name=rel_data["target"],
                entity_type="unknown",
            )
            relationship = EntityRelationship(
                source_entity_id=source_entity.id,
                target_entity_id=target_entity.id,
                relationship_type=rel_data.get("type", "associated"),
                description=rel_data.get("description"),
                confidence=float(rel_data.get("confidence", 0.5)),
            )
            session.add(relationship)

        # Process anomalies
        for anomaly_data in result.get("anomalies", []):
            anomaly = Anomaly(
                document_id=chunk.document_id,
                anomaly_type=anomaly_data.get("type", "unknown"),
                description=anomaly_data.get("description", ""),
                severity=anomaly_data.get("severity", "low"),
                confidence=float(anomaly_data.get("confidence", 0.5)),
                evidence=anomaly_data.get("evidence", "")[:1000],
            )
            session.add(anomaly)

        return result

    except json.JSONDecodeError as e:
        log.warning("triage_json_error", chunk_id=chunk.id, error=str(e))
        return None
    except Exception as e:
        log.error("triage_error", chunk_id=chunk.id, error=str(e))
        return None


async def run_triage(limit: int | None = None) -> dict:
    """Run triage on all chunked documents."""
    async with async_session_factory() as session:
        query = (
            select(Document)
            .where(Document.status == "chunked")
        )
        if limit:
            query = query.limit(limit)

        doc_result = await session.execute(query)
        documents = doc_result.scalars().all()

        total_chunks = 0
        total_entities = 0
        total_anomalies = 0
        max_priority = 0.0

        for doc in documents:
            chunk_result = await session.execute(
                select(Chunk).where(
                    Chunk.document_id == doc.id,
                )
            )
            chunks = chunk_result.scalars().all()

            doc_priority_scores = []

            for chunk in chunks:
                result = await triage_chunk(chunk, session)
                if result:
                    priority = float(result.get("priority_score", 0.0))
                    doc_priority_scores.append(priority)
                    total_entities += len(result.get("entities", []))
                    total_anomalies += len(result.get("anomalies", []))

                total_chunks += 1

                # Rate limiting: don't overwhelm the API
                await asyncio.sleep(0.5)

            # Update document priority (max of chunk priorities)
            if doc_priority_scores:
                doc.priority_score = max(doc_priority_scores)
                max_priority = max(max_priority, doc.priority_score)

            doc.status = "triaged"
            log.info(
                "document_triaged",
                document_id=doc.id,
                chunks=len(chunks),
                priority=doc.priority_score,
            )

        await session.commit()

    stats = {
        "documents_triaged": len(documents),
        "chunks_analyzed": total_chunks,
        "entities_found": total_entities,
        "anomalies_found": total_anomalies,
        "max_priority": max_priority,
    }
    log.info("triage_complete", **stats)
    return stats
