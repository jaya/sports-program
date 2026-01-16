from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.achievement import NotifyResponse
from app.services.achievement_service import AchievementService

router = APIRouter(tags=["Achievement"])

AchievementServiceDep = Annotated[AchievementService, Depends()]


@router.post(
    "/achievements/notify/{program_name}/{cycle_reference}",
    response_model=NotifyResponse,
    status_code=status.HTTP_200_OK,
)
async def notify(
    program_name: str,
    cycle_reference: str,
    service: AchievementServiceDep,
):
    return await service.notify(
        program_name=program_name,
        cycle_reference=cycle_reference,
    )
