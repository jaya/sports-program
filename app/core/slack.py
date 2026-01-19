from slack_bolt.async_app import AsyncApp
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings

from app.core.config import settings
from app.core.database import async_session
from app.core.slack_stores import SQLAlchemyInstallationStore, SQLAlchemyStateStore

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
