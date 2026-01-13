import logging

from slack_bolt import Ack, BoltContext

from app.core.slack import slack_app
from app.interfaces.slack.slack_actions import (
    create_program_action,
    list_programs_action,
)
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
        logger.error(f"Erro ao criar o programa: {str(e)}", exc_info=True)
        await context.say(f"Erro ao criar o programa: {str(e)}")
        return

    await context.say(
        blocks=blocks, text=f"Programa {program.name} criado com sucesso!"
    )


@slack_app.command("/list-programs")
async def handle_list_programs(ack: Ack, command: dict, context: BoltContext):
    """
    Handle the /list-programs command.
    """
    await ack()
    db = context["db"]
    try:
        programs = await list_programs_action(db)
        blocks = create_programs_list_blocks(programs)
    except Exception as e:
        logger.error(f"Erro ao listar os programas: {str(e)}", exc_info=True)
        await context.say(f"Erro ao listar os programas: {str(e)}")
        return
    await context.say(blocks=blocks, text="Programas")
