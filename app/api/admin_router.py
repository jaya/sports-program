from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.services.cron_service import CronService

router = APIRouter(prefix="/admin", tags=["Admin"])

CronServiceDep = Annotated[CronService, Depends()]


@router.post(
    "/run-monthly-job",
    status_code=status.HTTP_200_OK,
)
async def run_monthly_job(
    service: CronServiceDep,
    cycle_reference: str | None = None,
):
    return await service.run_monthly_job(cycle_reference)


@router.post(
    "/close-all-cycles",
    status_code=status.HTTP_200_OK,
)
async def close_all_cycles(
    service: CronServiceDep,
    cycle_reference: str | None = None,
):
    return await service.close_all_cycles(cycle_reference)


@router.post(
    "/notify-all-achievements",
    status_code=status.HTTP_200_OK,
)
async def notify_all_achievements(
    service: CronServiceDep,
    cycle_reference: str | None = None,
):
    return await service.notify_all_achievements(cycle_reference)
