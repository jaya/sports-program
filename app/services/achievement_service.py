import logging
from typing import Annotated

from fastapi import Depends

from app.core.config import settings
from app.core.slack import slack_app
from app.exceptions.business import (
    BusinessRuleViolationError,
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


class AchievementService:
    def __init__(
        self,
        achievement_repo: Annotated[AchievementRepository, Depends()],
        user_repo: Annotated[UserRepository, Depends()],
        program_repo: Annotated[ProgramRepository, Depends()],
    ):
        self.achievement_repo = achievement_repo
        self.user_repo = user_repo
        self.program_repo = program_repo

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
        existing_user_ids = await self.achievement_repo.find_existing_user_ids(
            program_id=achievement_batch.program_id,
            cycle_reference=achievement_batch.cycle_reference,
            user_ids=achievement_batch.user_ids,
        )

        if existing_user_ids:
            logging.warning(f"Skipped {len(existing_user_ids)} existing users")

        new_user_ids = [
            uid for uid in achievement_batch.user_ids if uid not in existing_user_ids
        ]

        if new_user_ids:
            db_achievements = [
                Achievement(
                    user_id=user_id,
                    program_id=achievement_batch.program_id,
                    cycle_reference=achievement_batch.cycle_reference,
                )
                for user_id in new_user_ids
            ]
            try:
                await self.achievement_repo.create_many(db_achievements)
            except Exception as e:
                raise DatabaseError() from e

        users = []
        if new_user_ids:
            users = await self.user_repo.find_all_by_ids(new_user_ids)

        return AchievementBatchResponse(
            total_created=len(new_user_ids),
            program_name=achievement_batch.program_name,
            cycle_reference=achievement_batch.cycle_reference,
            users=[str(user.display_name) for user in users],
        )

    async def notify(
        self,
        program_name: str,
        cycle_reference: str,
    ) -> NotifyResponse:
        notification_channel = settings.SLACK_NOTIFICATION_CHANNEL
        if not notification_channel:
            raise BusinessRuleViolationError(
                "SLACK_NOTIFICATION_CHANNEL not configured in .env"
            )

        program = await self.program_repo.find_by_name(program_name)
        if not program:
            raise EntityNotFoundError("Program", program_name)

        pending = await self.achievement_repo.find_pending_notification(
            program_id=program.id,
            cycle_reference=cycle_reference,
        )

        if not pending:
            return NotifyResponse(
                total_notified=0,
                message="No pending achievements to notify.",
            )

        slack_mentions = [f"<@{ach.user.slack_id}>" for ach in pending]
        user_names = [ach.user.display_name for ach in pending]
        program_name = pending[0].program.name

        mentions = ", ".join(slack_mentions)
        message = (
            f"{mentions}! Parabéns por completarem o desafio {program_name} "
            f"no ciclo {cycle_reference}!"
        )

        try:
            await slack_app.client.chat_postMessage(
                channel=notification_channel,
                text=message,
            )
        except Exception as e:
            logging.error(f"Error sending Slack message: {e}")
            raise ExternalServiceError(
                service="Slack",
                message="Failed to send notification"
            ) from e

        achievement_ids = [ach.id for ach in pending]
        await self.achievement_repo.mark_as_notified(achievement_ids)

        return NotifyResponse(
            total_notified=len(pending),
            message=message,
            users=user_names,
        )
