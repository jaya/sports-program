import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.program import Program
from app.repositories.slack_installation_repository import SlackInstallationRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_slack_client_for_program(
    db: AsyncSession,
    program: Program,
) -> AsyncGenerator[AsyncWebClient | None, None]:
    if not program.team_id and not program.enterprise_id:
        logger.warning(
            f"Program {program.id} ({program.name}) has no team_id or enterprise_id"
        )
        yield None
        return

    repo = SlackInstallationRepository(db)
    installation = await repo.get_by_team_or_enterprise(
        program.team_id, program.enterprise_id
    )

    if not installation:
        logger.warning(
            f"Installation not found for program {program.id} "
            f"(team_id={program.team_id}, enterprise_id={program.enterprise_id})"
        )
        yield None
        return

    client = AsyncWebClient(token=installation.bot_token)
    try:
        yield client
    finally:
        if hasattr(client, 'session') and client.session:
            await client.session.close()
