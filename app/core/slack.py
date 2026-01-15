from slack_bolt.async_app import AsyncApp

from app.core.config import settings

slack_app = AsyncApp(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET,
)


@slack_app.middleware
async def inject_db_session(context, next):
    from app.core.database import async_session

    async with async_session() as db:
        context["db"] = db
        await next()
