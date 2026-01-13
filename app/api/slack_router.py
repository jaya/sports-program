from fastapi import APIRouter, Request
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from app.core.slack import slack_app
# Import handlers to register them with the app
import app.interfaces.slack.slack_handlers  # noqa: F401

router = APIRouter(prefix="/slack", tags=["slack"])
app_handler = AsyncSlackRequestHandler(slack_app)


@router.post("/events")
async def slack_events(request: Request):
    return await app_handler.handle(request)
