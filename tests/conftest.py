import asyncio

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from watchdog.models import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite session for testing (no pgvector)."""
    # Use a real postgres for integration tests; this is for unit tests
    # For unit tests, we mock the session
    from unittest.mock import AsyncMock
    session = AsyncMock(spec=AsyncSession)
    yield session
