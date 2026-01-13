import logging
import re
from datetime import date

from slack_bolt import Ack, BoltContext

from app.core.slack import slack_app
from app.interfaces.slack.actions import create_program_action, register_activity_action
from app.interfaces.slack.views import (
    activity_registered_blocks,
    create_program_success_blocks,
    error_blocks,
    invalid_date_blocks,
)
from app.schemas.activity_schema import ActivityCreate

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def parse_activity_date(text: str) -> tuple[str, str | None]:
    """
    Parse activity description and date from text.

    Extracts date in @DD/MM format and converts to ISO format (YYYY-MM-DD).
    If no date is found, uses today's date.
    If the date is invalid, returns None for the date.

    Args:
        text: The input text containing description and optional @DD/MM date

    Returns:
        Tuple of (description, iso_date or None if invalid)
    """
    # Pattern to match @DD/MM format
    date_pattern = r"@(\d{1,2})/(\d{1,2})"
    match = re.search(date_pattern, text)

    # Clean up description first (remove date pattern and bot mention)
    description = re.sub(date_pattern, "", text).strip()
    description = re.sub(r"<@[A-Z0-9]+>", "", description).strip()
    description = re.sub(r"\s+", " ", description)

    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        try:
            # Use current year
            activity_date = date(date.today().year, month, day)
            return description, activity_date.isoformat()
        except ValueError:
            # Invalid date (e.g., 31/02, 45/13)
            return description, None
    else:
        activity_date = date.today()
        return description, activity_date.isoformat()


@slack_app.command("/create-program")
async def handle_create_program(ack: Ack, command: dict, context: BoltContext):
    """
    Handle the /create-program command.
    """
    await ack()
    channel_id = command.get("channel_id")
    program_name = command.get("text")

    if not program_name:
        await context.say(
            "Por favor, forneça um nome para o programa. Exemplo: `/create-program <nome-do-programa>`"
        )
        return

    db = context["db"]

    try:
        program = await create_program_action(db, program_name, channel_id)

        blocks = create_program_success_blocks(
            program.name, program.slack_channel, program.start_date, program.end_date
        )
    except Exception as e:
        await context.say(f"Erro ao criar o programa: {str(e)}")
        return

    await context.say(
        blocks=blocks, text=f"Programa {program.name} criado com sucesso!"
    )


@slack_app.event("app_mention")
async def handle_app_mention(event: dict, context: BoltContext):
    text = event.get("text", "")
    user_id = event.get("user")
    channel_id = event.get("channel")
    files = event.get("files", [{}])
    if len(files) > 0:
        evidence_url = files[0].get("url_private")

    description, activity_date = parse_activity_date(text)

    if activity_date is None:
        blocks = invalid_date_blocks()
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Data inválida!",
        )
        return

    try:
        await register_activity_action(
            db=context["db"],
            slack_channel=channel_id,
            slack_user_id=user_id,
            activity_create=ActivityCreate(
                description=description,
                performed_at=activity_date,
                evidence_url=evidence_url,
            ),
        )

        blocks = activity_registered_blocks(description, activity_date)
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Atividade registrada!",
        )
    except Exception as e:
        blocks = error_blocks(str(e))
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Erro ao registrar atividade",
        )
        return


@slack_app.event("message")
async def handle_message_events(body):
    logger.info(body)
