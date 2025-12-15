from fastapi import APIRouter, Depends, Header, Path
from typing import List, Annotated

from app.schemas.activity import ActivityCreate, ActivityResponse
from app.services.activities.create import Create
from app.services.activities.find_by_user import FindByUser
from app.services.activities.find_by_user_and_program import FindByUserAndProgram

router = APIRouter(tags=["Activity"])

CreateServiceDep = Annotated[Create, Depends()]
FindByUserServiceDep = Annotated[FindByUser, Depends()]
FindByUserAndProgramServiceDep = Annotated[FindByUserAndProgram, Depends()]


@router.get("/activities", response_model=List[ActivityResponse])
async def get_activities_by_user(
    service: FindByUserServiceDep,
    x_slack_user_id: str = Header(...),
):
    return await service.execute(slack_id=x_slack_user_id)


@router.get("/programs/{program_id}/activities", response_model=List[ActivityResponse])
async def get_activities_by_user_and_program(
    service: FindByUserAndProgramServiceDep,
    program_id: int = Path(..., title="ID Program", ge=1),
    x_slack_user_id: str = Header(...),
):
    return await service.execute(program_id, x_slack_user_id)


@router.post("/programs/{program_id}/activities", response_model=ActivityResponse)
async def create_activity(
    service: CreateServiceDep,
    activity_create: ActivityCreate,
    program_id: int = Path(..., title="ID Program", ge=1),
    x_slack_user_id: str = Header(...),
):
    return await service.execute(activity_create, program_id, x_slack_user_id)
