from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


@pytest.mark.anyio
async def test_base_repository_create():
    session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository(session, User)
    obj = User(id=1, slack_id="U1")

    result = await repo.create(obj)

    session.add.assert_called_once_with(obj)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(obj)
    assert result == obj

@pytest.mark.anyio
async def test_base_repository_create_rollback_on_exception():
    session = AsyncMock(spec=AsyncSession)
    session.commit.side_effect = Exception("DB Error")
    repo = BaseRepository(session, User)
    obj = User(id=1)

    with pytest.raises(Exception, match="DB Error"):
        await repo.create(obj)

    session.rollback.assert_called_once()

@pytest.mark.anyio
async def test_base_repository_get_by_id():
    session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository(session, User)
    obj = User(id=1)

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = obj
    session.execute.return_value = mock_result

    result = await repo.get_by_id(1)

    session.execute.assert_called_once()
    assert result == obj

@pytest.mark.anyio
async def test_base_repository_get_all():
    session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository(session, User)
    objs = [User(id=1), User(id=2)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = objs
    session.execute.return_value = mock_result

    result = await repo.get_all()

    session.execute.assert_called_once()
    assert result == objs

@pytest.mark.anyio
async def test_base_repository_update_success():
    session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository(session, User)
    obj = User(id=1, slack_id="U1", display_name="Updated Name")

    result = await repo.update(obj)

    session.add.assert_called_once_with(obj)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(obj)
    assert result == obj

@pytest.mark.anyio
async def test_base_repository_update_rollback_on_exception():
    session = AsyncMock(spec=AsyncSession)
    session.commit.side_effect = Exception("Update Error")
    repo = BaseRepository(session, User)
    obj = User(id=1)

    with pytest.raises(Exception, match="Update Error"):
        await repo.update(obj)

    session.rollback.assert_called_once()

@pytest.mark.anyio
async def test_base_repository_create_many():
    session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository(session, User)
    objs = [User(id=1), User(id=2)]

    result = await repo.create_many(objs)

    session.add_all.assert_called_once_with(objs)
    session.commit.assert_called_once()
    assert result == objs

@pytest.mark.anyio
async def test_base_repository_create_many_empty():
    session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository(session, User)

    result = await repo.create_many([])

    session.add_all.assert_not_called()
    assert result == []

@pytest.mark.anyio
async def test_base_repository_create_many_rollback_on_exception():
    session = AsyncMock(spec=AsyncSession)
    session.commit.side_effect = Exception("DB Error")
    repo = BaseRepository(session, User)
    objs = [User(id=1)]

    with pytest.raises(Exception, match="DB Error"):
        await repo.create_many(objs)

    session.rollback.assert_called_once()
