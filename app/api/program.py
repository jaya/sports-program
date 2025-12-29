from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated

from app.exceptions.business import EntityNotFoundError
from app.schemas.program import ProgramCreate, ProgramResponse, ProgramUpdate
from app.services.programs.find_all import FindAll
from app.services.programs.create import Create
from app.services.programs.find_by_name import FindByName
from app.services.programs.update import Update

router = APIRouter(tags=["Program"])

FindAllServiceDep = Annotated[FindAll, Depends()]
CreateServiceDep = Annotated[Create, Depends()]
FindByNameServiceDep = Annotated[FindByName, Depends()]
UpdateServiceDep = Annotated[Update, Depends()]


@router.get("/programs", response_model=List[ProgramResponse])
async def get_programs(service: FindAllServiceDep):
    return await service.execute()


@router.get("/programs/{slack_channel}/{name}", response_model=ProgramResponse)
async def get_program_by_name(name: str, slack_channel: str, service: FindByNameServiceDep):
    program = await service.execute(name, slack_channel)
    if not program:
        raise EntityNotFoundError("Program", name)
    return program


@router.post("/programs", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(program: ProgramCreate, service: CreateServiceDep):
    return await service.execute(program)


@router.patch("/programs/{program_id}", response_model=ProgramResponse, status_code=status.HTTP_200_OK)
async def update_program(program_id: int, program: ProgramUpdate, service: UpdateServiceDep):
    return await service.execute(program_id, program)
