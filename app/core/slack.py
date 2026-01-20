import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.oauth.async_callback_options import AsyncCallbackOptions
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings

from app.core.config import settings
from app.core.database import async_session
from app.core.slack_stores import SQLAlchemyInstallationStore, SQLAlchemyStateStore

logger = logging.getLogger(__name__)


async def oauth_success(args):
    installation = args.installation
    logger.info(
        "Slack OAuth SUCCESS: Team: %s, User: %s",
        installation.team_id,
        installation.user_id,
    )
    return await args.default_callback_options.success(args)


async def oauth_failure(args):
    logger.error(
        "Slack OAuth FAILURE: Reason: %s, State: %s",
        args.reason,
        args.request.query.get("state"),
    )
    return await args.default_callback_options.failure(args)


oauth_settings = AsyncOAuthSettings(
    client_id=settings.SLACK_CLIENT_ID,
    client_secret=settings.SLACK_CLIENT_SECRET,
    scopes=settings.SLACK_SCOPES.split(","),
    installation_store=SQLAlchemyInstallationStore(async_session),
    state_store=SQLAlchemyStateStore(
        async_session, expiration_seconds=settings.SLACK_STATE_EXPIRATION_SECONDS
    ),
    install_path=settings.SLACK_INSTALL_PATH,
    redirect_uri_path=settings.SLACK_REDIRECT_URI_PATH,
    callback_options=AsyncCallbackOptions(
        success=oauth_success,
        failure=oauth_failure,
    ),
)

slack_app = AsyncApp(
    signing_secret=settings.SLACK_SIGNING_SECRET,
    oauth_settings=oauth_settings,
)


@slack_app.middleware
async def inject_db_session(context, next):
    async with async_session() as db:
        context["db"] = db
        await next()
