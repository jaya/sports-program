from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time

from app.interfaces.slack.slack_actions import (
    create_program_action,
    list_programs_action,
)
from app.schemas.program_schema import ProgramResponse


@pytest.fixture
def mock_service():
    service = AsyncMock()
    return service


@freeze_time("2026-01-01 12:00:00")
@pytest.mark.anyio
async def test_create_program_calculates_dates_correctly(mock_service):
    # Setup
    expected_response = ProgramResponse(
        id=1,
        name="Jaya In Moviment",
        slack_channel="C123",
        start_date=datetime(2026, 1, 1, 12, 0, 0),
        end_date=datetime(2026, 1, 31, 12, 0, 0),
        created_at=datetime.now(),
    )
    mock_service.create.return_value = expected_response

    # Action
    result = await create_program_action(mock_service, "Jaya In Moviment", "C123")

    # Assert
    mock_service.create.assert_awaited_once()

    call_args = mock_service.create.call_args.args[0]

    assert call_args.name == "Jaya In Moviment"
    assert call_args.start_date == datetime(2026, 1, 1, 12, 0, 0)
    assert call_args.end_date == datetime(2026, 1, 31, 12, 0, 0)
    assert result == expected_response


@pytest.mark.anyio
async def test_list_programs_returns_all(mock_service):
    # Setup
    mock_list = [
        ProgramResponse(
            id=1,
            name="A",
            slack_channel="C",
            created_at=datetime.now(),
            start_date=datetime.now(),
            end_date=datetime.now(),
        )
    ]
    mock_service.find_all.return_value = mock_list

    # Action
    result = await list_programs_action(mock_service)

    # Assert
    mock_service.find_all.assert_awaited_once()
    assert result == mock_list
    assert len(result) == 1
