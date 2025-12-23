from fastapi import APIRouter, Depends, Header, Path, Query, status
from fastapi.responses import JSONResponse
from typing import List, Annotated

from app.schemas.activity import (
    ActivityCreate,
    ActivityResponse,
    ActivitySummaryResponse,
    ActivityUpdate,
)
from app.services.activities.create import Create
from app.services.activities.update import Update
from app.services.activities.find_by_user import FindByUser
from app.services.activities.find_by_user_and_program import FindByUserAndProgram

router = APIRouter(tags=["Activity"])

CreateServiceDep = Annotated[Create, Depends()]
UpdateServiceDep = Annotated[Update, Depends()]
FindByUserServiceDep = Annotated[FindByUser, Depends()]
FindByUserAndProgramServiceDep = Annotated[FindByUserAndProgram, Depends()]


@router.get("/activities", response_model=List[ActivityResponse])
async def get_activities_by_user(
    service: FindByUserServiceDep,
    x_slack_user_id: str = Header(..., title="ID Slack User"),
    reference_date: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
):
    return await service.execute(x_slack_user_id, reference_date)


@router.patch(
    "/activities/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ActivitySummaryResponse
)
async def update_activity(
    service: UpdateServiceDep,
    activity_update: ActivityUpdate,
    id: int = Path(..., title="Activity ID"),
    x_slack_user_id: str = Header(..., title="ID Slack User"),
):
    summary = await service.execute(activity_update, id, x_slack_user_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=summary.model_dump(),
        headers={"Location": f"/activities/{summary.id}"}
    )


@router.get("/programs/{slack_channel}/activities", response_model=List[ActivityResponse])
async def get_activities_by_user_and_program(
    service: FindByUserAndProgramServiceDep,
    slack_channel: str = Path(..., title="Program Slack Channel"),
    x_slack_user_id: str = Header(..., title="ID Slack User"),
    reference_date: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
):
    return await service.execute(slack_channel, x_slack_user_id, reference_date)


@router.post(
    "/programs/{slack_channel}/activities",
    status_code=status.HTTP_201_CREATED,
    response_model=ActivitySummaryResponse
)
async def create_activity(
    service: CreateServiceDep,
    activity_create: ActivityCreate,
    slack_channel: str = Path(..., title="Program Slack Channel"),
    x_slack_user_id: str = Header(..., title="ID Slack User"),
):
    summary = await service.execute(activity_create, slack_channel, x_slack_user_id)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=summary.model_dump(),
        headers={"Location": f"/activities/{summary.id}"}
    )
