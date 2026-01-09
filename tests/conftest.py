import pytest
import anyio
from app.models.base import Base

@pytest.fixture
def anyio_backend():
    return "asyncio"
