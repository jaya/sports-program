from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.program import ProgramCreate
from app.models.program import Program
from app.core.database import get_db
from app.services.programs.find_by_name import FindByName


class Create:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        program_find_by_name: FindByName = Depends()
    ):
        self.db = db
        self.program_find_by_name = program_find_by_name

    async def execute(self, program: ProgramCreate):
        program_found = await self.program_find_by_name.execute(program.name)
        if program_found:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program with this name already exists"
            )

        if program.end_date is not None and program.end_date <= program.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start Date greater then End Date"
            )

        db_program = Program(name=program.name, slack_channel=program.slack_channel,
                             start_date=program.start_date, end_date=program.end_date)
        self.db.add(db_program)
        try:
            await self.db.commit()
            await self.db.refresh(db_program)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred: {str(e)}"
            )
        return db_program
