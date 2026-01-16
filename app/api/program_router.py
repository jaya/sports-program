from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.exceptions.business import EntityNotFoundError
from app.orchestrators.close_cycle import CloseCycle
from app.schemas.achievement import AchievementBatchResponse
from app.schemas.program_schema import ProgramCreate, ProgramResponse, ProgramUpdate
from app.services.program_service import ProgramService

router = APIRouter(tags=["Program"])

CloseCycleServiceDep = Annotated[CloseCycle, Depends()]
ProgramServiceDep = Annotated[ProgramService, Depends()]


@router.get("/programs", response_model=list[ProgramResponse])
async def get_programs(service: ProgramServiceDep):
    return await service.find_all()


@router.get("/programs/{slack_channel}/{name}", response_model=ProgramResponse)
async def get_program_by_slack_channel_and_name(name: str, slack_channel: str, service: ProgramServiceDep):
    program = await service.find_by_name_and_slack_channel(name, slack_channel)
    if not program:
        raise EntityNotFoundError("Program", name)
    return program


@router.post("/programs", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(program: ProgramCreate, service: ProgramServiceDep):
    return await service.create(program)


@router.patch("/programs/{program_id}", response_model=ProgramResponse, status_code=status.HTTP_200_OK)
async def update_program(program_id: int, program: ProgramUpdate, service: ProgramServiceDep):
    return await service.update(program_id, program)


@router.post(
    "/programs/{program_name}/close-cycle/{cycle_reference}",
    response_model=AchievementBatchResponse | None,
    status_code=status.HTTP_200_OK
)
async def close_cycle(
    program_name: str,
    cycle_reference: str,
    service: CloseCycleServiceDep
):
    return await service.execute(program_name, cycle_reference)
