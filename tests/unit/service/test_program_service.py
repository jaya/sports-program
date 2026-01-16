import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta

from app.services.program_service import ProgramService
from app.repositories.program_repository import ProgramRepository
from app.schemas.program_schema import ProgramCreate, ProgramResponse, ProgramUpdate
from app.models.program import Program
from app.exceptions.business import DuplicateEntityError, BusinessRuleViolationError, DatabaseError, EntityNotFoundError

@pytest.fixture
def mock_program_repo():
    return AsyncMock(spec=ProgramRepository)

@pytest.fixture
def program_service(mock_program_repo):
    return ProgramService(program_repo=mock_program_repo)

@pytest.mark.anyio
async def test_create_program_success(program_service, mock_program_repo):
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    program_create = ProgramCreate(
        name="Test Program",
        slack_channel="C12345",
        start_date=start_date,
        end_date=end_date
    )
    
    mock_program_repo.find_by_name_and_slack_channel.return_value = None
    
    db_program = Program(
        id=1,
        name=program_create.name,
        slack_channel=program_create.slack_channel,
        start_date=program_create.start_date,
        end_date=program_create.end_date,
        created_at=datetime.now()
    )
    mock_program_repo.create.return_value = db_program
    
    result = await program_service.create(program_create)
    
    assert isinstance(result, ProgramResponse)
    assert result.name == program_create.name
    assert result.slack_channel == program_create.slack_channel
    mock_program_repo.find_by_name_and_slack_channel.assert_called_once_with(
        program_create.name, program_create.slack_channel
    )
    mock_program_repo.create.assert_called_once()

@pytest.mark.anyio
async def test_create_program_duplicate_error(program_service, mock_program_repo):
    program_create = ProgramCreate(
        name="Duplicate Program",
        slack_channel="C12345",
        start_date=datetime.now()
    )
    
    mock_program_repo.find_by_name_and_slack_channel.return_value = Program(id=1, name="Duplicate Program")
    
    with pytest.raises(DuplicateEntityError) as exc_info:
        await program_service.create(program_create)
    
    assert "Program with name 'Duplicate Program' already exists." in str(exc_info.value)
    mock_program_repo.create.assert_not_called()

@pytest.mark.anyio
async def test_create_program_invalid_dates_error(program_service, mock_program_repo):
    start_date = datetime.now()
    end_date = start_date - timedelta(days=1) 
    program_create = ProgramCreate(
        name="Invalid Dates Program",
        slack_channel="C12345",
        start_date=start_date,
        end_date=end_date
    )
    
    mock_program_repo.find_by_name_and_slack_channel.return_value = None
    
    with pytest.raises(BusinessRuleViolationError) as exc_info:
        await program_service.create(program_create)
    
    assert "Start Date greater then End Date" in str(exc_info.value)
    mock_program_repo.create.assert_not_called()

@pytest.mark.anyio
async def test_create_program_database_error(program_service, mock_program_repo):
    program_create = ProgramCreate(
        name="DB Error Program",
        slack_channel="C12345",
        start_date=datetime.now()
    )
    
    mock_program_repo.find_by_name_and_slack_channel.return_value = None
    mock_program_repo.create.side_effect = Exception("Connection lost")
    
    with pytest.raises(DatabaseError):
        await program_service.create(program_create)
    
    mock_program_repo.create.assert_called_once()

@pytest.mark.anyio
async def test_update_program_success(program_service, mock_program_repo):
    program_id = 1
    existing_program = Program(
        id=program_id,
        name="Old Name",
        slack_channel="C1",
        start_date=datetime.now(),
        created_at=datetime.now()
    )
    program_update = ProgramUpdate(name="New Name")
    
    mock_program_repo.get_by_id.return_value = existing_program
    mock_program_repo.find_by_name.return_value = None
    mock_program_repo.update.return_value = existing_program 
    
    result = await program_service.update(program_id, program_update)
    
    assert result.name == "New Name"
    mock_program_repo.get_by_id.assert_called_once_with(program_id)
    mock_program_repo.update.assert_called_once()

@pytest.mark.anyio
async def test_update_program_not_found(program_service, mock_program_repo):
    mock_program_repo.get_by_id.return_value = None
    
    with pytest.raises(EntityNotFoundError):
        await program_service.update(1, ProgramUpdate(name="Name"))

@pytest.mark.anyio
async def test_update_program_duplicate_name(program_service, mock_program_repo):
    program_id = 1
    existing_program = Program(id=program_id, name="My Program", slack_channel="C1")
    other_program = Program(id=2, name="Duplicate Name", slack_channel="C1")
    program_update = ProgramUpdate(name="Duplicate Name")
    
    mock_program_repo.get_by_id.return_value = existing_program
    mock_program_repo.find_by_name.return_value = other_program
    
    with pytest.raises(DuplicateEntityError):
        await program_service.update(program_id, program_update)

@pytest.mark.anyio
async def test_update_program_invalid_dates_error(program_service, mock_program_repo):
    program_id = 1
    existing_program = Program(
        id=program_id, 
        name="P1", 
        slack_channel="C1", 
        start_date=datetime.now()
    )
    start_date = datetime.now() + timedelta(days=10)
    end_date = datetime.now()
    program_update = ProgramUpdate(start_date=start_date, end_date=end_date)
    
    mock_program_repo.get_by_id.return_value = existing_program
    
    with pytest.raises(BusinessRuleViolationError):
        await program_service.update(program_id, program_update)

@pytest.mark.anyio
async def test_update_program_database_error(program_service, mock_program_repo):
    program_id = 1
    existing_program = Program(id=program_id, name="P1", slack_channel="C1")
    program_update = ProgramUpdate(name="New Name")
    
    mock_program_repo.get_by_id.return_value = existing_program
    mock_program_repo.find_by_name.return_value = None
    mock_program_repo.update.side_effect = Exception("DB Error")
    
    with pytest.raises(DatabaseError):
        await program_service.update(program_id, program_update)

@pytest.mark.anyio
async def test_find_all_programs(program_service, mock_program_repo):
    programs = [
        Program(id=1, name="P1", slack_channel="C1", start_date=datetime.now(), created_at=datetime.now()),
        Program(id=2, name="P2", slack_channel="C2", start_date=datetime.now(), created_at=datetime.now())
    ]
    mock_program_repo.get_all.return_value = programs
    
    result = await program_service.find_all()
    
    assert len(result) == 2
    assert result[0].name == "P1"
    mock_program_repo.get_all.assert_called_once()

@pytest.mark.anyio
async def test_find_program_by_id_success(program_service, mock_program_repo):
    program = Program(id=1, name="P1")
    mock_program_repo.get_by_id.return_value = program
    
    result = await program_service.find_by_id(1)
    
    assert result == program
    mock_program_repo.get_by_id.assert_called_once_with(1)

@pytest.mark.anyio
async def test_find_program_by_slack_channel(program_service, mock_program_repo):
    programs = [Program(id=1, name="P1", slack_channel="C1")]
    mock_program_repo.find_by_slack_channel.return_value = programs
    
    result = await program_service.find_by_slack_channel("C1")
    
    assert result == programs
    mock_program_repo.find_by_slack_channel.assert_called_once_with("C1")

@pytest.mark.anyio
async def test_find_program_by_name(program_service, mock_program_repo):
    program = Program(id=1, name="P1")
    mock_program_repo.find_by_name.return_value = program
    
    result = await program_service.find_by_name("P1")
    
    assert result == program
    mock_program_repo.find_by_name.assert_called_once_with("P1")
