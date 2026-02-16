from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from watchdog.models.base import Base, TimestampMixin, new_uuid


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(50))  # "doj" or "huggingface"
    filename: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    page_count: Mapped[int | None] = mapped_column(Integer)
    ocr_text: Mapped[str | None] = mapped_column(Text)
    ocr_method: Mapped[str | None] = mapped_column(String(50))  # "pymupdf", "tesseract"
    status: Mapped[str] = mapped_column(String(50), default="downloaded")  # downloaded, ocr_done, chunked, privacy_filtered, triaged
    priority_score: Mapped[float | None] = mapped_column(Float)

    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    images: Mapped[list["Image"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    videos: Mapped[list["Video"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Chunk(Base, TimestampMixin):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))
    privacy_filtered: Mapped[bool] = mapped_column(Boolean, default=False)
    pii_found: Mapped[str | None] = mapped_column(Text)  # JSON list of PII types found
    filtered_text: Mapped[str | None] = mapped_column(Text)  # text after PII redaction

    document: Mapped["Document"] = relationship(back_populates="chunks")
    entity_mentions: Mapped[list["EntityMention"]] = relationship(back_populates="chunk", cascade="all, delete-orphan")


class Entity(Base, TimestampMixin):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(500), index=True)
    entity_type: Mapped[str] = mapped_column(String(100))  # person, organization, location, etc.
    description: Mapped[str | None] = mapped_column(Text)
    mention_count: Mapped[int] = mapped_column(Integer, default=0)

    mentions: Mapped[list["EntityMention"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    relationships_as_source: Mapped[list["EntityRelationship"]] = relationship(
        back_populates="source_entity", foreign_keys="EntityRelationship.source_entity_id"
    )
    relationships_as_target: Mapped[list["EntityRelationship"]] = relationship(
        back_populates="target_entity", foreign_keys="EntityRelationship.target_entity_id"
    )


class EntityMention(Base, TimestampMixin):
    __tablename__ = "entity_mentions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), index=True)
    chunk_id: Mapped[str] = mapped_column(String(36), ForeignKey("chunks.id"), index=True)
    context_snippet: Mapped[str | None] = mapped_column(Text)

    entity: Mapped["Entity"] = relationship(back_populates="mentions")
    chunk: Mapped["Chunk"] = relationship(back_populates="entity_mentions")


class EntityRelationship(Base, TimestampMixin):
    __tablename__ = "entity_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    source_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), index=True)
    target_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    source_entity: Mapped["Entity"] = relationship(
        back_populates="relationships_as_source", foreign_keys=[source_entity_id]
    )
    target_entity: Mapped["Entity"] = relationship(
        back_populates="relationships_as_target", foreign_keys=[target_entity_id]
    )


class Anomaly(Base, TimestampMixin):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    anomaly_type: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(50))  # low, medium, high, critical
    confidence: Mapped[float] = mapped_column(Float)
    evidence: Mapped[str | None] = mapped_column(Text)  # relevant text excerpt

    document: Mapped["Document"] = relationship()


class ProcessingJob(Base, TimestampMixin):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    job_type: Mapped[str] = mapped_column(String(100))  # download, ocr, chunk, privacy, triage
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, running, completed, failed
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id"))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    document: Mapped["Document | None"] = relationship()


class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    service: Mapped[str] = mapped_column(String(100))  # "anthropic"
    model: Mapped[str] = mapped_column(String(100))
    operation: Mapped[str] = mapped_column(String(200))  # "privacy_filter", "triage"
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id"))

    document: Mapped["Document | None"] = relationship()


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    page_number: Mapped[int | None] = mapped_column(Integer)
    file_path: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    document: Mapped["Document"] = relationship(back_populates="images")


class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    file_path: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    document: Mapped["Document"] = relationship(back_populates="videos")
