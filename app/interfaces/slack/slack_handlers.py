from slack_bolt import Ack, BoltContext

from app.core.slack import slack_app
from app.interfaces.slack.actions import create_program_action
from app.interfaces.slack.views import create_program_success_blocks


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
