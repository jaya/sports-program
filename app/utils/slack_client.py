from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.program import Program
from app.repositories.slack_installation_repository import SlackInstallationRepository

logger = structlog.get_logger()


@asynccontextmanager
async def get_slack_client_for_program(
    db: AsyncSession,
    program: Program,
) -> AsyncGenerator[AsyncWebClient | None]:
    if not program.team_id and not program.enterprise_id:
        logger.warning(
            "Program has no team_id or enterprise_id",
            program_id=program.id,
            program_name=program.name,
        )
        yield None
        return

    repo = SlackInstallationRepository(db)
    installation = await repo.get_by_team_or_enterprise(
        program.team_id, program.enterprise_id
    )

    if not installation:
        logger.warning(
            "Installation not found for program",
            program_id=program.id,
            team_id=program.team_id,
            enterprise_id=program.enterprise_id,
        )
        yield None
        return

    client = AsyncWebClient(token=installation.bot_token)
    try:
        yield client
    finally:
        if hasattr(client, "session") and client.session:
            await client.session.close()
