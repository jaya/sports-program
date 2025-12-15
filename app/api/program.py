from fastapi import APIRouter, Depends
from typing import List, Annotated

from app.schemas.program import ProgramCreate, ProgramResponse
from app.services.programs.find_all import FindAll
from app.services.programs.create import Create

router = APIRouter(tags=["Program"])

FindAllServiceDep = Annotated[FindAll, Depends()]
CreateServiceDep = Annotated[Create, Depends()]


@router.get("/program", response_model=List[ProgramResponse])
async def get_programs(service: FindAllServiceDep):
    return await service.execute()


@router.post("/program", response_model=ProgramResponse)
async def create_program(program: ProgramCreate, service: CreateServiceDep):
    return await service.execute(program)
