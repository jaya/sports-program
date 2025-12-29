from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.business import DuplicateEntityError, BusinessRuleViolationError, DatabaseError
from app.schemas.program import ProgramCreate
from app.models.program import Program
from app.core.database import get_db
from app.services.programs.find_by_name_and_slack_channel import FindByNameAndSlackChannel


class Create:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
            program_find_by_name_slack_channel: FindByNameAndSlackChannel = Depends()
    ):
        self.db = db
        self.program_find_by_name_slack_channel = program_find_by_name_slack_channel

    async def execute(self, program: ProgramCreate):
        program_found = await self.program_find_by_name_slack_channel.execute(program.name, program.slack_channel)
        if program_found:
            raise DuplicateEntityError("Program", "name", program.name)

        if program.end_date is not None and program.end_date <= program.start_date:
            raise BusinessRuleViolationError(
                "Start Date greater then End Date")

        db_program = Program(name=program.name, slack_channel=program.slack_channel,
                             start_date=program.start_date, end_date=program.end_date)
        self.db.add(db_program)
        try:
            await self.db.commit()
            await self.db.refresh(db_program)
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e
        return db_program
