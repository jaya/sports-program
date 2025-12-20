from fastapi import APIRouter, Depends, HTTPException
from typing import List, Annotated

from app.schemas.program import ProgramCreate, ProgramResponse
from app.services.programs.find_all import FindAll
from app.services.programs.create import Create
from app.services.programs.find_by_name import FindByName

router = APIRouter(tags=["Program"])

FindAllServiceDep = Annotated[FindAll, Depends()]
CreateServiceDep = Annotated[Create, Depends()]
FindByNameServiceDep = Annotated[FindByName, Depends()]


@router.get("/programs", response_model=List[ProgramResponse])
async def get_programs(service: FindAllServiceDep):
    return await service.execute()


@router.get("/programs/{slack_channel}/{name}", response_model=ProgramResponse)
async def get_program_by_name(name: str, slack_channel: str, service: FindByNameServiceDep):
    program = await service.execute(name, slack_channel)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@router.post("/programs", response_model=ProgramResponse)
async def create_program(program: ProgramCreate, service: CreateServiceDep):
    return await service.execute(program)
