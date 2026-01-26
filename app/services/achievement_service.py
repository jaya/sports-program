from typing import Annotated

import structlog
from fastapi import Depends

from app.core.slack import slack_app
from app.exceptions.business import (
    DatabaseError,
    EntityNotFoundError,
    ExternalServiceError,
)
from app.models.achievement import Achievement
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.program_repository import ProgramRepository
from app.repositories.user_repository import UserRepository
from app.schemas.achievement import (
    AchievementBatchCreate,
    AchievementBatchResponse,
    AchievementCreate,
    NotifyResponse,
)
from app.services.activity_service import ActivityService


async def _send_slack_notification(channel: str, message: str) -> None:
    try:
        await slack_app.client.chat_postMessage(
            channel=channel,
            text=message,
        )
    except Exception as e:
        logger.error("Slack notification failed", channel=channel, error=str(e))
        raise ExternalServiceError(
            service="Slack", message="Failed to send notification"
        ) from e


def _build_message(
    achievements: list[Achievement], cycle_reference: str
) -> tuple[str, list[str]]:
    slack_mentions = [f"<@{ach.user.slack_id}>" for ach in achievements]
    user_names = [ach.user.display_name for ach in achievements]
    program_name = achievements[0].program.name

    mentions = ", ".join(slack_mentions)
    message = (
        f"{mentions}! Parabéns por completarem o desafio {program_name} "
        f"no ciclo {cycle_reference}!"
    )

    return message, user_names


logger = structlog.get_logger()


class AchievementService:
    def __init__(
        self,
        achievement_repo: Annotated[AchievementRepository, Depends()],
        user_repo: Annotated[UserRepository, Depends()],
        program_repo: Annotated[ProgramRepository, Depends()],
        activity_service: Annotated[ActivityService, Depends()],
    ):
        self.achievement_repo = achievement_repo
        self.user_repo = user_repo
        self.program_repo = program_repo
        self.activity_service = activity_service

    async def create(
        self,
        achievement_create: AchievementCreate,
        program_id: int,
        user_id: int,
    ):
        db_achievement = Achievement(
            user_id=user_id,
            program_id=program_id,
            cycle_reference=achievement_create.cycle_reference,
        )
        try:
            return await self.achievement_repo.create(db_achievement)
        except Exception as e:
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
                    "Database error while creating achievements",
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
        program_name: str,
        cycle_reference: str,
    ) -> NotifyResponse:
        logger.info(
            "Starting achievement notification",
            program=program_name,
            cycle_reference=cycle_reference,
        )
        program = await self.program_repo.find_by_name(program_name)
        if not program:
            raise EntityNotFoundError("Program", program_name)

        pending = await self.achievement_repo.find_pending_notification(
            program_id=program.id,
            cycle_reference=cycle_reference,
        )

        if not pending:
            logger.info(
                "No achievements pending notification for this cycle",
                program=program_name,
                cycle_reference=cycle_reference,
            )
            return NotifyResponse(
                total_notified=0,
                message="No pending achievements to notify.",
            )

        message, user_names = _build_message(pending, cycle_reference)
        await _send_slack_notification(program.slack_channel, message)
        await self.achievement_repo.mark_as_notified([ach.id for ach in pending])
        logger.info(
            "Slack notifications sent for achievements", total_notified=len(pending)
        )

        return NotifyResponse(
            total_notified=len(pending),
            message=message,
            users=user_names,
        )

    async def close_cycle(
        self, program_name: str, cycle_reference: str
    ) -> AchievementBatchResponse | None:
        logger.info(
            "Closing program cycle",
            program=program_name,
            cycle=cycle_reference,
        )
        program = await self.program_repo.find_by_name(program_name)
        if not program:
            raise EntityNotFoundError("Program", program_name)

        user_ids = await self.activity_service.find_all_user_by_program_completed(
            program_name=program_name, cycle_reference=cycle_reference
        )

        if not user_ids:
            logger.debug(
                "No users eligible for cycle closure",
                program=program_name,
                cycle=cycle_reference,
            )
            return None

        batch = AchievementBatchCreate(
            user_ids=user_ids,
            program_id=program.id,
            program_name=program.name,
            cycle_reference=cycle_reference,
        )

        return await self.create_batch(batch)
