from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.interfaces.slack.slack_handlers import (
    handle_app_mention,
    handle_create_program,
    handle_list_activities,
    handle_list_programs,
    handle_message_events,
)
from app.models.program import Program

HANDLERS_PATH = "app.interfaces.slack.slack_handlers"
CREATE_PROGRAM_ACTION = f"{HANDLERS_PATH}.create_program_action"
CREATE_PROGRAM_SUCCESS_BLOCKS = f"{HANDLERS_PATH}.create_program_success_blocks"
GET_PROGRAM_SERVICE = f"{HANDLERS_PATH}.get_program_service"
LIST_PROGRAMS_ACTION = f"{HANDLERS_PATH}.list_programs_action"
CREATE_PROGRAMS_LIST_BLOCKS = f"{HANDLERS_PATH}.create_programs_list_blocks"
PARSE_REFERENCE_DATE = f"{HANDLERS_PATH}.parse_reference_date"
LIST_ACTIVITIES_ACTION = f"{HANDLERS_PATH}.list_activities_action"
ACTIVITIES_LIST_BLOCKS = f"{HANDLERS_PATH}.activities_list_blocks"
GET_ACTIVITY_SERVICE = f"{HANDLERS_PATH}.get_activity_service"
PARSE_ACTIVITY_DATE = f"{HANDLERS_PATH}.parse_activity_date"
REGISTER_ACTIVITY_ACTION = f"{HANDLERS_PATH}.register_activity_action"
ACTIVITY_REGISTERED_BLOCKS = f"{HANDLERS_PATH}.activity_registered_blocks"
HELP_BLOCKS = f"{HANDLERS_PATH}.help_blocks"


def create_mock_command(text="", channel_id="C123", user_id="U123"):
    return {"channel_id": channel_id, "user_id": user_id, "text": text}


def create_mock_event(
    text="", channel="C123", user="U123", files=None, channel_type=None
):
    return {
        "text": text,
        "user": user,
        "channel": channel,
        "files": files or [{}],
        "channel_type": channel_type,
    }


@pytest.fixture
def mock_ack():
    return AsyncMock()


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.say = AsyncMock()
    context.client.chat_postEphemeral = AsyncMock()
    context.__getitem__.return_value = MagicMock()
    return context


@pytest.mark.anyio
async def test_handle_create_program_success(mock_ack, mock_context):
    command = create_mock_command(text="New Program")

    with (
        patch(
            CREATE_PROGRAM_ACTION,
            new_callable=AsyncMock,
        ) as mock_create_action,
        patch(CREATE_PROGRAM_SUCCESS_BLOCKS) as mock_create_blocks,
        patch(GET_PROGRAM_SERVICE),
    ):
        program = Program(
            id=1,
            name="New Program",
            slack_channel="C123",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
        )
        mock_create_action.return_value = program
        mock_create_blocks.return_value = [
            {"type": "section", "text": {"type": "mrkdwn", "text": "Success"}}
        ]

        await handle_create_program(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_create_action.assert_awaited_once()
        mock_context.say.assert_awaited_once()
        args, kwargs = mock_context.say.call_args
        assert (
            "created successfully" in kwargs.get("text", "")
            or kwargs.get("blocks") is not None
        )


@pytest.mark.anyio
async def test_handle_create_program_no_name(mock_ack, mock_context):
    command = create_mock_command()

    await handle_create_program(mock_ack, command, mock_context)

    mock_ack.assert_awaited_once()
    mock_context.client.chat_postEphemeral.assert_awaited_once()
    _, kwargs = mock_context.client.chat_postEphemeral.call_args
    assert "undefined program name" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_create_program_error(mock_ack, mock_context):
    command = create_mock_command(text="New Program")

    with (
        patch(
            CREATE_PROGRAM_ACTION,
            new_callable=AsyncMock,
        ) as mock_create_action,
        patch(GET_PROGRAM_SERVICE),
    ):
        mock_create_action.side_effect = Exception("Test Error")

        await handle_create_program(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Error on creating program" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_list_programs_success(mock_ack, mock_context):
    command = create_mock_command()

    with (
        patch(
            LIST_PROGRAMS_ACTION,
            new_callable=AsyncMock,
        ) as mock_list_action,
        patch(CREATE_PROGRAMS_LIST_BLOCKS) as mock_list_blocks,
        patch(GET_PROGRAM_SERVICE),
    ):
        mock_list_action.return_value = []
        mock_list_blocks.return_value = []

        await handle_list_programs(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_list_action.assert_awaited_once()
        mock_context.client.chat_postEphemeral.assert_awaited_once()


@pytest.mark.anyio
async def test_handle_list_programs_error(mock_ack, mock_context):
    command = create_mock_command()

    with (
        patch(
            LIST_PROGRAMS_ACTION,
            new_callable=AsyncMock,
        ) as mock_list_action,
        patch(GET_PROGRAM_SERVICE),
    ):
        mock_list_action.side_effect = Exception("List Error")

        await handle_list_programs(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Error on listing programs" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_list_activities_success(mock_ack, mock_context):
    command = create_mock_command(text="today")

    with (
        patch(PARSE_REFERENCE_DATE) as mock_parse_date,
        patch(
            LIST_ACTIVITIES_ACTION,
            new_callable=AsyncMock,
        ) as mock_action,
        patch(ACTIVITIES_LIST_BLOCKS) as mock_blocks,
        patch(GET_ACTIVITY_SERVICE),
    ):
        mock_parse_date.return_value = date(2023, 1, 1)
        mock_action.return_value = []
        mock_blocks.return_value = []

        await handle_list_activities(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_action.assert_awaited_once()
        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Activities:" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_list_activities_invalid_date(mock_ack, mock_context):
    command = create_mock_command(text="invalid")

    with patch(PARSE_REFERENCE_DATE) as mock_parse_date:
        mock_parse_date.side_effect = Exception("Invalid Date")

        await handle_list_activities(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Invalid date!" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_list_activities_error(mock_ack, mock_context):
    command = create_mock_command(text="last week")

    with (
        patch(PARSE_REFERENCE_DATE) as mock_parse_date,
        patch(
            LIST_ACTIVITIES_ACTION,
            new_callable=AsyncMock,
        ) as mock_action,
        patch(GET_ACTIVITY_SERVICE),
    ):
        mock_parse_date.return_value = date(2023, 1, 1)
        mock_action.side_effect = Exception("Service Error")

        await handle_list_activities(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Error on listing activities" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_app_mention_success(mock_context):
    event = create_mock_event(text="Ran 5km", files=[{"url_private": "http://img.com"}])

    with (
        patch(PARSE_ACTIVITY_DATE) as mock_parse_date,
        patch(
            REGISTER_ACTIVITY_ACTION,
            new_callable=AsyncMock,
        ) as mock_action,
        patch(ACTIVITY_REGISTERED_BLOCKS) as mock_blocks,
        patch(GET_ACTIVITY_SERVICE),
    ):
        mock_parse_date.return_value = ("Ran 5km", date.today())
        # mock activity return object
        activity_mock = MagicMock()
        activity_mock.count_month = 5
        mock_action.return_value = activity_mock
        mock_blocks.return_value = []

        await handle_app_mention(event, mock_context)

        mock_action.assert_awaited_once()
        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Activity registered!" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_app_mention_invalid_date(mock_context):
    event = create_mock_event(text="Ran 5km")

    with patch(PARSE_ACTIVITY_DATE) as mock_parse_date:
        mock_parse_date.return_value = ("Ran 5km", None)

        await handle_app_mention(event, mock_context)

        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Invalid date!" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_app_mention_error(mock_context):
    event = create_mock_event(text="Ran 5km today")

    with (
        patch(PARSE_ACTIVITY_DATE) as mock_parse_date,
        patch(
            REGISTER_ACTIVITY_ACTION,
            new_callable=AsyncMock,
        ) as mock_action,
        patch(GET_ACTIVITY_SERVICE),
    ):
        mock_parse_date.return_value = ("Ran 5km", date(2023, 1, 1))
        mock_action.side_effect = Exception("Error")

        await handle_app_mention(event, mock_context)

        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Error on registering activity" in kwargs.get("text", "")


@pytest.mark.anyio
async def test_handle_app_mention_help(mock_context):
    event = create_mock_event(text="help")

    with (
        patch(PARSE_ACTIVITY_DATE) as mock_parse_date,
        patch(HELP_BLOCKS) as mock_help_blocks,
    ):
        mock_parse_date.return_value = ("help", None)
        mock_help_blocks.return_value = [
            {"type": "section", "text": {"type": "mrkdwn", "text": "Help"}}
        ]

        await handle_app_mention(event, mock_context)

        mock_context.client.chat_postEphemeral.assert_awaited_once()
        _, kwargs = mock_context.client.chat_postEphemeral.call_args
        assert "Help" in kwargs.get("text")
        assert kwargs.get("blocks")


@pytest.mark.anyio
async def test_handle_message_events_help(mock_context):
    event = create_mock_event(text="help", channel_type="im")

    with patch(HELP_BLOCKS) as mock_help_blocks:
        mock_help_blocks.return_value = [
            {"type": "section", "text": {"type": "mrkdwn", "text": "Help"}}
        ]

        await handle_message_events(event, mock_context)

        mock_context.say.assert_awaited_once()
        _, kwargs = mock_context.say.call_args
        assert "Help" in kwargs.get("text")
        assert kwargs.get("blocks")


@pytest.mark.anyio
async def test_handle_message_events_default(mock_context):
    event = create_mock_event(text="hello", channel_type="im")

    await handle_message_events(event, mock_context)

    mock_context.say.assert_awaited_once()
    args, _ = mock_context.say.call_args
    assert "You can send `help`" in args[0]
