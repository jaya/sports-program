from fastapi import APIRouter, Depends, Header, Path
from typing import List, Annotated

from app.models.activity import ActivityCreate, ActivityRead
from app.services.activity import ActivityService

router = APIRouter(tags=["Activity"])

ActivityServiceDep = Annotated[ActivityService, Depends()]

@router.get("/activities", response_model=List[ActivityRead])
async def get_activities_by_user(
    service: ActivityServiceDep,
    x_slack_user_id: str = Header(...),
):
    return await service.find_activities_by_user(slack_id=x_slack_user_id)


@router.get("/programs/{program_id}/activities", response_model=List[ActivityRead])
async def get_activities_by_user_and_program(
    service: ActivityServiceDep,
    program_id: int = Path(..., title="ID Program", ge=1),
    x_slack_user_id: str = Header(...),
):
    return await service.find_activities_by_user_and_program(program_id, x_slack_user_id)


@router.post("/programs/{program_id}/activities", response_model=ActivityRead)
async def create_activity(
    service: ActivityServiceDep,
    activity_create: ActivityCreate,
    program_id: int = Path(..., title="ID Program", ge=1),
    x_slack_user_id: str = Header(...),
):
    return await service.insert_activity(activity_create, program_id, x_slack_user_id)
