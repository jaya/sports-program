import logging

from slack_bolt import Ack, BoltContext

from app.core.slack import slack_app
from app.interfaces.slack.slack_actions import (
    create_program_action,
    list_activities_action,
    list_programs_action,
    register_activity_action,
)
from app.interfaces.slack.slack_factories import (
    get_activity_service,
    get_program_service,
)
from app.interfaces.slack.slack_views import (
    activities_list_blocks,
    activity_registered_blocks,
    create_program_success_blocks,
    create_programs_list_blocks,
    error_blocks,
    invalid_date_blocks,
    invalid_reference_date_blocks,
)
from app.schemas.activity_schema import ActivityCreate
from app.utils.parsers import parse_activity_date, parse_reference_date

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@slack_app.command("/create-program-rafa")
async def handle_create_program(ack: Ack, command: dict, context: BoltContext):
    """
    Handle the /create-program command.
    """
    await ack()
    channel_id = command.get("channel_id")
    user_id = command.get("user_id")
    program_name = command.get("text")

    if not program_name:
        blocks = error_blocks(
            "Please, provide a program name. Example: `/create-program <program-name>`"
        )
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Error on creating program because of undefined program name",
        )
        return

    db = context["db"]

    try:
        service = get_program_service(db)
        program = await create_program_action(service, program_name, channel_id)

        blocks = create_program_success_blocks(
            program.name, program.slack_channel, program.start_date, program.end_date
        )
    except Exception as e:
        logger.error(f"Error on creating program: {str(e)}", exc_info=True)
        blocks = error_blocks(str(e))
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Error on creating program",
        )
        return

    await context.say(
        blocks=blocks, text=f"Program {program.name} successfully created!"
    )


@slack_app.command("/list-programs-rafa")
async def handle_list_programs(ack: Ack, command: dict, context: BoltContext):
    """
    Handle the /list-programs command.
    """
    await ack()
    db = context["db"]
    channel_id = command.get("channel_id")
    user_id = command.get("user_id")
    try:
        service = get_program_service(db)
        programs = await list_programs_action(service)
        blocks = create_programs_list_blocks(programs)
    except Exception as e:
        logger.error(f"Error listing programs: {str(e)}", exc_info=True)
        blocks = error_blocks(str(e))
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Error on listing programs",
        )
        return
    await context.client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        blocks=blocks,
        text="Programs",
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
            text="Invalid date!",
        )
        return

    db = context["db"]

    try:
        service = get_activity_service(db)
        activities = await list_activities_action(
            service, channel_id, user_id, reference_date
        )

        blocks = activities_list_blocks(activities)

        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Activities:",
        )

    except Exception as e:
        blocks = error_blocks(str(e))
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Error on listing activities",
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
            text="Invalid date!",
        )
        return

    try:
        service = get_activity_service(context["db"])
        activity = await register_activity_action(
            service,
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
            text="Activity registered!",
        )
    except Exception as e:
        blocks = error_blocks(str(e))
        await context.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Error on registering activity",
        )
        return


@slack_app.event("message")
async def handle_message_events(body):
    logger.info(body)
