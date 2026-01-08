from slack_bolt.async_app import AsyncApp
from app.core.config import settings

slack_app = AsyncApp(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET,
)
