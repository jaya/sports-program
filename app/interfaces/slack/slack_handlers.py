from slack_bolt import Ack, BoltContext
from app.core.slack import slack_app
from app.interfaces.slack.actions import create_program_action


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

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Programa criado com sucesso!",
                    "emoji": True,
                },
            },
            {"type": "divider"},
        ]

        p_start_date = program.start_date.strftime("%d/%m/%Y")
        p_end_date = "N/A"
        if program.end_date:
            p_end_date = program.end_date.strftime("%d/%m/%Y")

        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{program.name}*\n:hash: Canal: <#{program.slack_channel}>\n:calendar: Início: {p_start_date}\n:checkered_flag: Fim: {p_end_date}",
                },
            }
        )
    except Exception as e:
        await context.say(f"Erro ao criar o programa: {str(e)}")
        return

    await context.say(
        blocks=blocks, text=f"Programa {program.name} criado com sucesso!"
    )
