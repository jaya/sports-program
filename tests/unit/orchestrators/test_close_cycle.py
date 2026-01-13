from unittest.mock import AsyncMock

import pytest

from app.exceptions.business import EntityNotFoundError
from app.models.program import Program
from app.orchestrators.close_cycle import CloseCycle
from app.schemas.achievement import AchievementBatchResponse
from app.services.achievement_service import AchievementService
from app.services.activity_service import ActivityService
from app.services.program_service import ProgramService


@pytest.fixture
def mock_program_service():
    return AsyncMock(spec=ProgramService)


@pytest.fixture
def mock_activity_service():
    return AsyncMock(spec=ActivityService)


@pytest.fixture
def mock_achievement_service():
    return AsyncMock(spec=AchievementService)


@pytest.fixture
def orchestrator(mock_program_service, mock_activity_service, mock_achievement_service):
    return CloseCycle(
        program_service=mock_program_service,
        activity_service=mock_activity_service,
        achievement_service=mock_achievement_service,
    )


@pytest.mark.anyio
async def test_close_cycle_execute_success(
    orchestrator, mock_program_service, mock_activity_service, mock_achievement_service
):
    mock_program_service.find_by_name.return_value = Program(id=1, name="P1")
    mock_activity_service.find_all_user_by_program_completed.return_value = [1, 2]

    expected_response = AchievementBatchResponse(
        total_created=2,
        program_name="P1",
        cycle_reference="2023-10",
        users=["U1", "U2"],
    )
    mock_achievement_service.create_batch.return_value = expected_response

    result = await orchestrator.execute("P1", "2023-10")

    assert result == expected_response
    mock_achievement_service.create_batch.assert_called_once()
    args, _ = mock_achievement_service.create_batch.call_args
    batch = args[0]
    assert batch.program_id == 1
    assert batch.user_ids == [1, 2]


@pytest.mark.anyio
async def test_close_cycle_execute_program_not_found(
    orchestrator, mock_program_service
):
    mock_program_service.find_by_name.return_value = None

    with pytest.raises(EntityNotFoundError):
        await orchestrator.execute("P1", "2023-10")


@pytest.mark.anyio
async def test_close_cycle_execute_no_users(
    orchestrator, mock_program_service, mock_activity_service, mock_achievement_service
):
    mock_program_service.find_by_name.return_value = Program(id=1, name="P1")
    mock_activity_service.find_all_user_by_program_completed.return_value = []

    result = await orchestrator.execute("P1", "2023-10")

    assert result is None
    mock_achievement_service.create_batch.assert_not_called()
