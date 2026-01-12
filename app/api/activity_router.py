from fastapi import APIRouter, Depends, Header, Path, Query, status, Response
from fastapi.responses import JSONResponse
from typing import List, Annotated

from app.schemas.activity_schema import (
    ActivityCreate,
    ActivityResponse,
    ActivitySummaryResponse,
    ActivityUpdate,
)
from app.services.activity_service import ActivityService

router = APIRouter(tags=["Activity"])

ActivityServiceDep = Annotated[ActivityService, Depends()]


@router.get("/activities", response_model=List[ActivityResponse])
async def get_activities_by_user(
    service: ActivityServiceDep,
    x_slack_user_id: str = Header(..., title="ID Slack User"),
    reference_date: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
):
    return await service.find_by_user(x_slack_user_id, reference_date)


@router.get("/activities/{id}", response_model=ActivityResponse)
async def get_activity_by_id(
    service: ActivityServiceDep,
    x_slack_user_id: str = Header(..., title="ID Slack User"),
    id: int = Path(..., title="Activity ID"),
):
    return await service.find_by_id(id, x_slack_user_id)


@router.patch(
    "/activities/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ActivitySummaryResponse,
)
async def update_activity(
    service: ActivityServiceDep,
    activity_update: ActivityUpdate,
    id: int = Path(..., title="Activity ID"),
    x_slack_user_id: str = Header(..., title="ID Slack User"),
):
    summary = await service.update(activity_update, id, x_slack_user_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=summary.model_dump(),
        headers={"Location": f"/activities/{summary.id}"},
    )


@router.delete("/activities/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    service: ActivityServiceDep,
    x_slack_user_id: str = Header(..., title="ID Slack User"),
    id: int = Path(..., title="Activity ID"),
):
    await service.delete(id, x_slack_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/programs/{slack_channel}/activities", response_model=List[ActivityResponse]
)
async def get_activities_by_user_and_program(
    service: ActivityServiceDep,
    slack_channel: str = Path(..., title="Program Slack Channel"),
    x_slack_user_id: str = Header(..., title="ID Slack User"),
    reference_date: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
):
    return await service.find_by_user_and_program(
        slack_channel, x_slack_user_id, reference_date
    )


@router.post(
    "/programs/{slack_channel}/activities",
    status_code=status.HTTP_201_CREATED,
    response_model=ActivitySummaryResponse,
)
async def create_activity(
    service: ActivityServiceDep,
    activity_create: ActivityCreate,
    slack_channel: str = Path(..., title="Program Slack Channel"),
    x_slack_user_id: str = Header(..., title="ID Slack User"),
):
    summary = await service.create(activity_create, slack_channel, x_slack_user_id)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=summary.model_dump(),
        headers={"Location": f"/activities/{summary.id}"},
    )
