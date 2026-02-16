"""Initial schema with all 10 tables

Revision ID: 001
Revises:
Create Date: 2026-02-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_url", sa.Text),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.Text),
        sa.Column("sha256", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("page_count", sa.Integer),
        sa.Column("ocr_text", sa.Text),
        sa.Column("ocr_method", sa.String(50)),
        sa.Column("status", sa.String(50), nullable=False, server_default="downloaded"),
        sa.Column("priority_score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("page_start", sa.Integer),
        sa.Column("page_end", sa.Integer),
        sa.Column("embedding", Vector(384)),
        sa.Column("privacy_filtered", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("pii_found", sa.Text),
        sa.Column("filtered_text", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "entities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False, index=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("mention_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "entity_mentions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False, index=True),
        sa.Column("chunk_id", sa.String(36), sa.ForeignKey("chunks.id"), nullable=False, index=True),
        sa.Column("context_snippet", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "entity_relationships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False, index=True),
        sa.Column("target_entity_id", sa.String(36), sa.ForeignKey("entities.id"), nullable=False, index=True),
        sa.Column("relationship_type", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "anomalies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("anomaly_type", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("evidence", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id")),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("service", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("operation", sa.String(200), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "images",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("page_number", sa.Integer),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "videos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("videos")
    op.drop_table("images")
    op.drop_table("expenses")
    op.drop_table("processing_jobs")
    op.drop_table("anomalies")
    op.drop_table("entity_relationships")
    op.drop_table("entity_mentions")
    op.drop_table("entities")
    op.drop_table("chunks")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector")
