import logging

from slack_bolt import Ack, BoltContext

from app.core.slack import slack_app
from app.interfaces.slack.slack_actions import (
    create_program_action,
    list_programs_action,
)
from app.interfaces.slack.slack_factories import get_program_service
from app.interfaces.slack.slack_views import (
    create_program_success_blocks,
    create_programs_list_blocks,
)

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
            "Please provide a program name. Example: `/create-program <program-name>`"
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
        await context.say(f"Error on creating program: {str(e)}")
        return

    await context.say(
        blocks=blocks, text=f"Program {program.name} successfully created!"
    )


@slack_app.command("/list-programs")
async def handle_list_programs(ack: Ack, command: dict, context: BoltContext):
    """
    Handle the /list-programs command.
    """
    await ack()
    db = context["db"]
    try:
        service = get_program_service(db)
        programs = await list_programs_action(service)
        blocks = create_programs_list_blocks(programs)
    except Exception as e:
        logger.error(f"Error listing programs: {str(e)}", exc_info=True)
        await context.say(f"Error listing programs: {str(e)}")
        return
    await context.say(blocks=blocks, text="Programs")
