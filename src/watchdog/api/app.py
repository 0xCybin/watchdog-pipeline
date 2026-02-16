from fastapi import FastAPI

from watchdog.api.routes import anomalies, documents, entities, pipeline, search, stats


def create_app() -> FastAPI:
    app = FastAPI(
        title="Watchdog Pipeline",
        description="Automated document analysis pipeline — ingest, OCR, chunk, embed, and triage large document dumps",
        version="0.1.0",
    )

    # Mount all route modules under /api/v1
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(anomalies.router, prefix="/api/v1")
    app.include_router(entities.router, prefix="/api/v1")
    app.include_router(stats.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(pipeline.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
