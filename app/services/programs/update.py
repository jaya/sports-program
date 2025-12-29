from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.business import EntityNotFoundError, DuplicateEntityError, BusinessRuleViolationError, DatabaseError
from app.core.database import get_db
from app.schemas.program import ProgramUpdate
from app.services.programs.find_by_id import FindById
from app.services.programs.find_by_name import FindByName


class Update:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        find_by_id: FindById = Depends(),
        find_by_name: FindByName = Depends()
    ):
        self.db = db
        self.find_by_id = find_by_id
        self.find_by_name = find_by_name

    async def execute(self, id: int, program_update: ProgramUpdate):
        db_program = await self.find_by_id.execute(id)

        if not db_program:
            raise EntityNotFoundError("Program", id)

        if program_update.name and program_update.name != db_program.name:
            existing_program = await self.find_by_name.execute(program_update.name)
            if existing_program and existing_program.id != id:
                raise DuplicateEntityError(
                    "Program", "name", program_update.name)

        update_data = program_update.model_dump(exclude_unset=True)

        start_date = update_data.get("start_date", db_program.start_date)
        end_date = update_data.get("end_date", db_program.end_date)

        if start_date and end_date and start_date > end_date:
            raise BusinessRuleViolationError(
                "Start Date greater then End Date")

        for key, value in update_data.items():
            setattr(db_program, key, value)

        self.db.add(db_program)
        try:
            await self.db.commit()
            await self.db.refresh(db_program)
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e

        return db_program
