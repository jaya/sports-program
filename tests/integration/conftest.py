import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from alembic import command
from alembic.config import Config

os.environ["ENV_SCOPE"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test-integration.db"

from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    assert "test-integration.db" in settings.DATABASE_URL, "Not using test database!"

    alembic_cfg = Config("alembic.ini")
    if os.path.exists("./test-integration.db"):
        os.remove("./test-integration.db")

    command.upgrade(alembic_cfg, "head")

    yield


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
