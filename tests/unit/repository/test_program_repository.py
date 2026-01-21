import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.program_repository import ProgramRepository
from app.models.program import Program

@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def program_repo(mock_session):
    return ProgramRepository(mock_session)

@pytest.mark.anyio
async def test_find_by_name_success(program_repo, mock_session):
    program_name = "Test Program"
    expected_program = Program(id=1, name=program_name, slack_channel="C123")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_program
    mock_session.execute.return_value = mock_result
    
    result = await program_repo.find_by_name(program_name)
    
    mock_session.execute.assert_called_once()
    assert result == expected_program
    assert result.name == program_name

@pytest.mark.anyio
async def test_find_by_name_not_found(program_repo, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await program_repo.find_by_name("Non-existent")
    
    mock_session.execute.assert_called_once()
    assert result is None

@pytest.mark.anyio
async def test_find_by_name_and_slack_channel_success(program_repo, mock_session):
    name = "Channel Program"
    channel = "C123"
    expected_program = Program(id=1, name=name, slack_channel=channel)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_program
    mock_session.execute.return_value = mock_result
    
    result = await program_repo.find_by_name_and_slack_channel(name, channel)

    mock_session.execute.assert_called_once()
    assert result == expected_program
    assert result.name == name
    assert result.slack_channel == channel


@pytest.mark.anyio
async def test_find_by_name_and_slack_channel_not_found(program_repo, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await program_repo.find_by_name_and_slack_channel("Test Name", "Non-existent")

    mock_session.execute.assert_called_once()
    assert result is None

@pytest.mark.anyio
async def test_find_by_slack_channel_success(program_repo, mock_session):
    channel = "C123"
    programs = [
        Program(id=1, name="P1", slack_channel=channel),
        Program(id=2, name="P2", slack_channel=channel)
    ]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = programs
    mock_session.execute.return_value = mock_result
    
    result = await program_repo.find_by_slack_channel(channel)

    mock_session.execute.assert_called_once()
    assert len(result) == 2
    assert result == programs


@pytest.mark.anyio
async def test_find_by_slack_channel_not_found(program_repo, mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await program_repo.find_by_slack_channel("Non-existent")

    mock_session.execute.assert_called_once()
    assert result == []
    assert len(result) == 0