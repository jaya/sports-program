from typing import Annotated

from fastapi import Depends

from app.exceptions.business import (
    BusinessRuleViolationError,
    DatabaseError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from app.models.program import Program
from app.repositories.program_repository import ProgramRepository
from app.schemas.program_schema import ProgramCreate, ProgramResponse, ProgramUpdate


class ProgramService:
    def __init__(self, program_repo: Annotated[ProgramRepository, Depends()]):
        self.program_repo = program_repo

    async def create(self, program: ProgramCreate) -> ProgramResponse:
        program_found = await self.program_repo.find_by_name_and_slack_channel(
            program.name, program.slack_channel
        )
        if program_found:
            raise DuplicateEntityError("Program", "name", program.name)
        if program.end_date is not None and program.end_date <= program.start_date:
            raise BusinessRuleViolationError("Start Date greater then End Date")

        db_program = Program(
            name=program.name,
            slack_channel=program.slack_channel,
            start_date=program.start_date.replace(
                hour=0, minute=0, second=1, microsecond=0
            ),
            end_date=program.end_date,
        )

        try:
            created = await self.program_repo.create(db_program)
            return ProgramResponse.model_validate(created)
        except Exception as e:
            raise DatabaseError() from e

    async def update(self, id: int, program_update: ProgramUpdate) -> ProgramResponse:
        db_program = await self.program_repo.get_by_id(id)
        if not db_program:
            raise EntityNotFoundError("Program", id)

        if program_update.name and program_update.name != db_program.name:
            existing = await self.program_repo.find_by_name(program_update.name)
            if existing and existing.id != id:
                raise DuplicateEntityError("Program", "name", program_update.name)

        update_data = program_update.model_dump(exclude_unset=True)

        if "start_date" in update_data and update_data["start_date"] is not None:
            update_data["start_date"] = update_data["start_date"].replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        start_date = update_data.get("start_date", db_program.start_date)
        end_date = update_data.get("end_date", db_program.end_date)

        if start_date and end_date and start_date > end_date:
            raise BusinessRuleViolationError("Start Date greater than End Date")

        for key, value in update_data.items():
            setattr(db_program, key, value)

        try:
            updated = await self.program_repo.update(db_program)
            return ProgramResponse.model_validate(updated)
        except Exception as e:
            raise DatabaseError() from e

    async def find_by_id(self, id: int) -> Program:
        return await self.program_repo.get_by_id(id)

    async def find_all(self) -> list[ProgramResponse]:
        return await self.program_repo.get_all()

    async def find_by_slack_channel(self, slack_channel: str) -> list[Program]:
        return await self.program_repo.find_by_slack_channel(slack_channel)

    async def find_by_name(self, name: str) -> Program:
        return await self.program_repo.find_by_name(name)