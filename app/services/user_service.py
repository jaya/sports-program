from typing import Annotated

import structlog
from fastapi import Depends

from app.core.slack import slack_app
from app.exceptions.business import (
    DatabaseError,
    DuplicateEntityError,
    ExternalServiceError,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate

logger = structlog.get_logger()

class UserService:
    def __init__(
        self,
        user_repo: Annotated[UserRepository, Depends()],
    ):
        self.user_repo = user_repo

    async def get_slack_display_name(self, slack_id: str) -> str:
        try:
            response = await slack_app.client.users_info(user=slack_id)

            if not response["ok"]:
                error = response.get("error", "unknown_error")
                logger.error("Failed to fetch user from Slack API", slack_id=slack_id, error=error)
                raise ExternalServiceError(
                    service="Slack",
                    message=f"Failed to fetch user: {error}"
                )

            user_info = response["user"]
            display_name = (
                user_info.get("profile", {}).get("display_name")
                or user_info.get("real_name")
                or user_info.get("name")
            )

            if not display_name:
                logger.error("Failed to fetch user from Slack API", slack_id=slack_id, error="No display name found")
                raise ExternalServiceError(
                    service="Slack",
                    message=f"User {slack_id} has no display name"
                )

            return display_name
        except Exception as e:
            if not isinstance(e, ExternalServiceError):
                logger.error("Failed to fetch user from Slack API", slack_id=slack_id, error=str(e))
            raise

    async def create(self, user: UserCreate):
        user_found = await self.user_repo.find_by_slack_id(user.slack_id)
        if user_found:
            logger.warning("User already exists", entity="User", slack_id=user.slack_id)
            raise DuplicateEntityError("User", "slack_id", user.slack_id)

        db_user = User(slack_id=user.slack_id, display_name=user.display_name)

        try:
            created = await self.user_repo.create(db_user)
            logger.info("User created successfully", slack_id=user.slack_id, display_name=user.display_name)
            return created
        except Exception as e:
            logger.error("Failed to create user", entity="User", error=str(e))
            raise DatabaseError() from e

    async def find_all(self):
        return await self.user_repo.get_all()

    async def find_by_slack_id(self, slack_id: str):
        return await self.user_repo.find_by_slack_id(slack_id)
