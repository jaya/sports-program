from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.business import BusinessRuleViolationError
from app.core.database import get_db
from app.services.activities.find_by_id import FindById
from app.utils.date_validator import is_within_allowed_window


class Delete:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        find_by_id: FindById = Depends(),
    ):
        self.db = db
        self.find_by_id = find_by_id

    async def execute(self, id: int, slack_id: str):
        activity = await self.find_by_id.execute(id, slack_id)

        if not is_within_allowed_window(activity.performed_at):
            raise BusinessRuleViolationError(
                "Activities can only be deleted within the current or previous month."
            )

        await self.db.delete(activity)
        await self.db.commit()
        return None
