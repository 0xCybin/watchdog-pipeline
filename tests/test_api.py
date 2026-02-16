import pytest
from httpx import ASGITransport, AsyncClient

from watchdog.api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestDocumentEndpoints:
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="Requires running Postgres")
    async def test_list_documents(self, client):
        response = await client.get("/api/v1/documents")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="Requires running Postgres")
    async def test_get_document_not_found(self, client):
        response = await client.get("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404


class TestSearchEndpoint:
    @pytest.mark.asyncio
    async def test_search_requires_query(self, client):
        response = await client.post("/api/v1/search", json={})
        assert response.status_code == 422  # Validation error
