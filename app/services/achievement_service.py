from typing import Annotated

import structlog
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.business import (
    DatabaseError,
    EntityNotFoundError,
    ExternalServiceError,
)
from app.models.achievement import Achievement
from app.models.program import Program
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.program_repository import ProgramRepository
from app.repositories.user_repository import UserRepository
from app.schemas.achievement import (
    AchievementBatchCreate,
    AchievementBatchResponse,
    AchievementCreate,
    AchievementCreateResponse,
    NotifyResponse,
)
from app.services.utils.reference_date import ReferenceDate
from app.utils.slack_client import get_slack_client_for_program

GOAL_ACTIVITIES = 12


def _build_message(
    achievements: list[Achievement], cycle_reference: str
) -> tuple[str, list[str]]:
    slack_mentions = [f"<@{ach.user.slack_id}>" for ach in achievements]
    user_names = [ach.user.display_name for ach in achievements]
    program_name = achievements[0].program.name

    mentions = ", ".join(slack_mentions)
    message = (
        f":tada: *Congratulations* {mentions}! :star2:\n\n"
        f"You've successfully completed the *{program_name}* challenge "
        f"for the *{cycle_reference}* cycle!\n\n"
        f":trophy: Keep up the amazing work! :muscle:"
    )

    return message, user_names


logger = structlog.get_logger()


class AchievementService:
    def __init__(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],
        achievement_repo: Annotated[AchievementRepository, Depends()],
        user_repo: Annotated[UserRepository, Depends()],
        program_repo: Annotated[ProgramRepository, Depends()],
        activity_repo: Annotated[ActivityRepository, Depends()],
    ):
        self.db = db
        self.achievement_repo = achievement_repo
        self.user_repo = user_repo
        self.program_repo = program_repo
        self.activity_repo = activity_repo

    async def create(
        self,
        achievement_create: AchievementCreate,
        program_id: int,
        user_id: int,
    ) -> AchievementCreateResponse | None:
        already_exists = await self.achievement_repo.user_has_achievement(
            user_id=user_id,
            program_id=program_id,
            cycle_reference=achievement_create.cycle_reference,
        )

        if already_exists:
            logger.info(
                "Achievement already exists",
                user_id={user_id},
                program_id={program_id},
                cycle={achievement_create.cycle_reference},
            )
            return None

        db_achievement = Achievement(
            user_id=user_id,
            program_id=program_id,
            cycle_reference=achievement_create.cycle_reference,
        )
        try:
            created = await self.achievement_repo.create(db_achievement)
            logger.info("Achievement created for user", user_id=user_id)
            return created
        except Exception as e:
            logger.exception(
                "Database error while creating achievement",
                program_id=program_id,
                user_id=user_id,
            )
            raise DatabaseError() from e

    async def create_batch(
        self, achievement_batch: AchievementBatchCreate
    ) -> AchievementBatchResponse:
        program_id = achievement_batch.program_id
        cycle_reference = achievement_batch.cycle_reference
        logger.info(
            "Starting achievement batch creation",
            program_id=program_id,
            cycle=cycle_reference,
        )
        existing_user_ids = await self.achievement_repo.find_existing_user_ids(
            program_id=program_id,
            cycle_reference=cycle_reference,
            user_ids=achievement_batch.user_ids,
        )

        if existing_user_ids:
            logger.debug(
                "Achievements skipped as they already exist",
                count=len(existing_user_ids),
            )

        new_user_ids = [
            uid for uid in achievement_batch.user_ids if uid not in existing_user_ids
        ]

        if new_user_ids:
            db_achievements = [
                Achievement(
                    user_id=user_id,
                    program_id=program_id,
                    cycle_reference=cycle_reference,
                )
                for user_id in new_user_ids
            ]
            try:
                await self.achievement_repo.create_many(db_achievements)
            except Exception as e:
                logger.exception(
                    "Database error while achievement batch creation",
                    program_id=program_id,
                    cycle_reference=cycle_reference,
                    total=len(new_user_ids),
                )
                raise DatabaseError() from e

        users = []
        if new_user_ids:
            users = await self.user_repo.find_all_by_ids(new_user_ids)

        logger.info(
            "Achievement batch completed",
            created=len(new_user_ids),
            skipped=len(existing_user_ids),
        )

        return AchievementBatchResponse(
            total_created=len(new_user_ids),
            program_name=achievement_batch.program_name,
            cycle_reference=cycle_reference,
            users=[str(user.display_name) for user in users],
        )

    async def notify_achievements(
        self,
        program_id: int,
        cycle_reference: str,
    ) -> NotifyResponse:
        logger.info(
            "Starting achievement notification",
            program=program_id,
            cycle_reference=cycle_reference,
        )
        program = await self.program_repo.get_by_id(program_id)

        if not program:
            raise EntityNotFoundError("Program", program_id)

        pending = await self.achievement_repo.find_pending_notification(
            program_id=program_id,
            cycle_reference=cycle_reference,
        )

        if not pending:
            logger.info(
                "No achievements pending notification for this cycle",
                program=program_id,
                cycle_reference=cycle_reference,
            )
            return NotifyResponse(
                total_notified=0,
                message="No pending achievements to notify.",
            )

        message, user_names = _build_message(pending, cycle_reference)
        await self._send_slack_notification(program, message)
        await self.achievement_repo.mark_as_notified([ach.id for ach in pending])
        logger.info(
            "Slack notifications sent for achievements", total_notified=len(pending)
        )

        return NotifyResponse(
            total_notified=len(pending),
            message=message,
            users=user_names,
        )

    async def _send_slack_notification(
        self, program: Program, message: str
    ) -> None:
        async with get_slack_client_for_program(self.db, program) as client:
            if not client:
                raise ExternalServiceError(
                    service="Slack",
                    message=f"Could not get client for program {program.name}. "
                    "Check if team_id/enterprise_id is set and installation exists."
                )

            try:
                await client.chat_postMessage(
                    channel=program.slack_channel,
                    text=message,
                )
            except Exception as e:
                logger.error("Error sending Slack message", error=str(e), message=message, channel=program.slack_channel)
                raise ExternalServiceError(
                    service="Slack", message="Failed to send notification"
                ) from e

    async def close_cycle(
        self, program_id: int, cycle_reference: str
    ) -> AchievementBatchResponse | None:
        logger.info(
            "Closing program cycle",
            program=program_id,
            cycle=cycle_reference,
        )
        program = await self.program_repo.get_by_id(program_id)
        if not program:
            raise EntityNotFoundError("Program", program_id)

        ref = ReferenceDate.from_str(cycle_reference)
        user_ids = await self.activity_repo.find_users_with_completed_program(
            program.id, ref.year, ref.month, GOAL_ACTIVITIES)

        if not user_ids:
            logger.debug(
                "No users eligible for cycle closure",
                program=program_id,
                cycle=cycle_reference,
            )
            return None

        batch = AchievementBatchCreate(
            user_ids=user_ids,
            program_id=program_id,
            program_name=program.name,
            cycle_reference=cycle_reference,
        )

        return await self.create_batch(batch)
