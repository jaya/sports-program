from slack_bolt import Ack, BoltContext
from app.core.slack import slack_app


@slack_app.command("/create-program")
async def handle_create_program(ack: Ack, command: dict, context: BoltContext):
    """
    Handle the /create-program command.
    """
    await ack()
    user_id = command.get("user_id")
    channel_name = command.get("channel_name")
    program_name = command.get("text")
    print(f"User ID: {user_id}")
    print(f"Channel Name: {channel_name}")
    await context.say(
        f"Olá! Recebi seu comando para criar o programa '{program_name}'. 🚀\nEm breve estarei funcional!"
    )
