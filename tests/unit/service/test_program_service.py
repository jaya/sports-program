from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models.program import Program
from app.repositories.program_repository import ProgramRepository
from app.schemas.program_schema import ProgramCreate, ProgramUpdate
from app.services.program_service import ProgramService


@pytest.fixture
def mock_program_repo():
    return AsyncMock(spec=ProgramRepository)


@pytest.fixture
def program_service(mock_program_repo):
    return ProgramService(program_repo=mock_program_repo)


@pytest.mark.anyio
async def test_create_program_sets_start_date_to_beginning_of_day(
    program_service, mock_program_repo
):
    # Setup
    input_date = datetime(2026, 1, 19, 15, 30, 45)  # 15:30:45
    program_create = ProgramCreate(
        name="Test Program", slack_channel="C12345", start_date=input_date
    )

    mock_program_repo.find_by_name_and_slack_channel.return_value = None

    with patch("app.services.program_service.Program") as mock_program_class:
        mock_instance = mock_program_class.return_value
        mock_instance.name = "Test Program"
        mock_instance.slack_channel = "C12345"
        mock_instance.start_date = input_date
        mock_instance.end_date = None
        mock_instance.id = 1
        mock_instance.created_at = datetime.now()

        mock_program_repo.create.return_value = mock_instance

        # Execute
        await program_service.create(program_create)

        # Assert
        # Verify the arguments passed to the Program constructor
        mock_program_class.assert_called_once()
        args, kwargs = mock_program_class.call_args
        actual_start_date = kwargs.get("start_date")

        # This assertion would fail without the logic to truncate the date
        assert actual_start_date.hour == 0
        assert actual_start_date.minute == 0
        assert actual_start_date.second == 0


@pytest.mark.anyio
async def test_update_program_sets_start_date_to_beginning_of_day(
    program_service, mock_program_repo
):
    # Setup
    input_date = datetime(2026, 1, 20, 10, 0, 0)
    program_update = ProgramUpdate(start_date=input_date)

    db_program = AsyncMock(spec=Program)
    db_program.id = 1
    db_program.name = "Old Name"
    db_program.slack_channel = "C123"
    db_program.start_date = datetime(2026, 1, 19, 0, 0, 0)
    db_program.end_date = None
    db_program.created_at = datetime.now()

    mock_program_repo.get_by_id.return_value = db_program
    mock_program_repo.update.return_value = db_program

    # Execute
    await program_service.update(1, program_update)

    # Assert
    # setattr should have been called with the truncated date
    assert db_program.start_date.hour == 0
    assert db_program.start_date.minute == 0
    assert db_program.start_date.second == 0
