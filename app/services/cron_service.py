import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends

from app.repositories.program_repository import ProgramRepository
from app.services.achievement_service import AchievementService


def _get_previous_month_reference() -> str:
    today = datetime.now(UTC)
    if today.month == 1:
        year = today.year - 1
        month = 12
    else:
        year = today.year
        month = today.month - 1
    return f"{year}-{month:02d}"


class CronService:
    def __init__(
        self,
        program_repo: Annotated[ProgramRepository, Depends()],
        achievement_service: Annotated[AchievementService, Depends()],
    ):
        self.program_repo = program_repo
        self.achievement_service = achievement_service
        self.logger = logging.getLogger(__name__)

    async def close_all_cycles(self, cycle_reference: str | None = None) -> dict:
        if cycle_reference is None:
            cycle_reference = _get_previous_month_reference()

        self.logger.info(f"Starting close_all_cycles for {cycle_reference}")

        programs = await self.program_repo.find_active_in_cycle(cycle_reference)
        results = {
            "cycle_reference": cycle_reference,
            "total_programs": len(programs),
            "success": [],
            "errors": [],
        }

        for program in programs:
            try:
                result = await self.achievement_service.close_cycle(
                    program_id=program.id,
                    cycle_reference=cycle_reference,
                )
                if result:
                    results["success"].append({
                        "program_id": program.id,
                        "program_name": program.name,
                        "achievements_created": result.total_created,
                    })
                else:
                    results["success"].append({
                        "program_id": program.id,
                        "program_name": program.name,
                        "achievements_created": 0,
                    })
            except Exception as e:
                self.logger.error(
                    f"Error closing cycle for program {program.id}: {e}"
                )
                results["errors"].append({
                    "program_id": program.id,
                    "program_name": program.name,
                    "error": str(e),
                })

        self.logger.info(
            f"close_all_cycles completed: {len(results['success'])} success, "
            f"{len(results['errors'])} errors"
        )
        return results

    async def notify_all_achievements(self, cycle_reference: str | None = None) -> dict:
        if cycle_reference is None:
            cycle_reference = _get_previous_month_reference()

        self.logger.info(
            f"Starting notify_all_achievements for {cycle_reference}")

        programs = await self.program_repo.find_active_in_cycle(cycle_reference)
        results = {
            "cycle_reference": cycle_reference,
            "total_programs": len(programs),
            "success": [],
            "errors": [],
        }

        for program in programs:
            try:
                result = await self.achievement_service.notify_achievements(
                    program_id=program.id,
                    cycle_reference=cycle_reference,
                )
                results["success"].append({
                    "program_id": program.id,
                    "program_name": program.name,
                    "total_notified": result.total_notified,
                })
            except Exception as e:
                self.logger.error(
                    f"Error notifying achievements for program {program.id}: {e}"
                )
                results["errors"].append({
                    "program_id": program.id,
                    "program_name": program.name,
                    "error": str(e),
                })

        self.logger.info(
            f"notify_all_achievements completed: {len(results['success'])} success, "
            f"{len(results['errors'])} errors"
        )
        return results

    async def run_monthly_job(self, cycle_reference: str | None = None) -> dict:
        if cycle_reference is None:
            cycle_reference = _get_previous_month_reference()

        self.logger.info(f"Starting monthly job for {cycle_reference}")

        close_results = await self.close_all_cycles(cycle_reference)

        notify_results = await self.notify_all_achievements(cycle_reference)

        combined_results = {
            "cycle_reference": cycle_reference,
            "close_cycle": close_results,
            "notify": notify_results,
        }

        self.logger.info(f"Monthly job completed for {cycle_reference}")
        return combined_results
