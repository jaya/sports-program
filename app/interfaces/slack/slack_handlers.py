import logging

from slack_bolt import Ack, BoltContext

from app.core.slack import slack_app
from app.interfaces.slack.actions import (
    create_program_action,
    list_activities_action,
    register_activity_action,
)
from app.interfaces.slack.views import (
    activities_list_blocks,
    activity_registered_blocks,
    create_program_success_blocks,
    error_blocks,
    invalid_date_blocks,
    invalid_reference_date_blocks,
)
from app.schemas.activity_schema import ActivityCreate
from app.utils.parsers import parse_activity_date, parse_reference_date

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


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
            "Por favor, forneça um nome para o programa.\n"
            "Exemplo: `/create-program <nome-do-programa>`"
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


@slack_app.command("/list-activities-rafa")
async def handle_list_activities(ack: Ack, command: dict, context: BoltContext):
    await ack()
    user_id = command.get("user_id")
    channel_id = command.get("channel_id")
    text = command.get("text", "")
    try:
        reference_date = parse_reference_date(text)
    except Exception:
        blocks = invalid_reference_date_blocks()
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Data inválida!",
        )
        return

    db = context["db"]

    try:
        activities = await list_activities_action(
            db, channel_id, user_id, reference_date
        )

        blocks = activities_list_blocks(activities)

        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Atividades:",
        )

    except Exception as e:
        blocks = error_blocks(str(e))
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Erro ao listar atividades",
        )
        return


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
        activity = await register_activity_action(
            db=context["db"],
            slack_channel=channel_id,
            slack_user_id=user_id,
            activity_create=ActivityCreate(
                description=description,
                performed_at=activity_date,
                evidence_url=evidence_url,
            ),
        )

        blocks = activity_registered_blocks(
            description, activity_date, activity.count_month
        )
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
