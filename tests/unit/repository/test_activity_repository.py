from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.repositories.activity_repository import ActivityRepository


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    return ActivityRepository(mock_session)


def mock_activity():
    return Activity(
        id=2,
        user_id=1,
        program_id=3,
        description="Test Activity",
        evidence_url=None,
        performed_at="2025-12-15T10:00:00Z",
        created_at="2025-12-15T10:00:00Z",
    )


@pytest.mark.anyio
async def test_find_by_user_id_and_date(repo, mock_session):
    activities = [mock_activity()]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = activities
    mock_session.execute.return_value = mock_result

    result = await repo.find_by_user_id_and_date(1, 2025, 12)

    mock_session.execute.assert_called_once()
    assert result.__len__() == 1
    assert result == activities


@pytest.mark.anyio
async def test_find_by_id_and_slack_id(repo, mock_session):
    activities = mock_activity()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = activities
    mock_session.execute.return_value = mock_result

    result = await repo.find_by_id_and_slack_id(2, "U123")

    mock_session.execute.assert_called_once()
    assert result == activities


@pytest.mark.anyio
async def test_find_by_user_id_and_slack_channel_and_date(repo, mock_session):
    activities = [mock_activity()]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = activities
    mock_session.execute.return_value = mock_result

    result = await repo.find_by_user_id_and_slack_channel_and_date(1, "C123", 2025, 12)

    mock_session.execute.assert_called_once()
    assert result.__len__() == 1
    assert result == activities


@pytest.mark.anyio
async def test_count_monthly(repo, mock_session):
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_result

    result = await repo.count_monthly(1, 2025, 12)

    mock_session.execute.assert_called_once()
    assert result == 0


@pytest.mark.anyio
async def test_check_activity_same_day(repo, mock_session):
    activity = mock_activity()

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = activity
    mock_session.execute.return_value = mock_result

    test_date = date(2025, 12, 15)

    result = await repo.check_activity_same_day(3, 1, test_date)

    mock_session.execute.assert_called()
    assert result == activity

    result_excluded = await repo.check_activity_same_day(3, 1, test_date, exclude_id=99)
    assert result_excluded == activity


@pytest.mark.anyio
async def test_find_users_with_completed_program(repo, mock_session):
    user_ids = [1, 2, 3]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = user_ids
    mock_session.execute.return_value = mock_result

    result = await repo.find_users_with_completed_program(1, 2025, 12, 10)

    mock_session.execute.assert_called()
    assert result == user_ids
