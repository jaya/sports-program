from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.interfaces.slack.slack_handlers import (
    handle_create_program,
    handle_list_programs,
)
from app.models.program import Program


@pytest.fixture
def mock_ack():
    return AsyncMock()


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.say = AsyncMock()
    context.__getitem__.return_value = MagicMock()
    return context


@pytest.mark.anyio
async def test_handle_create_program_success(mock_ack, mock_context):
    command = {"channel_id": "C123", "text": "New Program"}

    with (
        patch(
            "app.interfaces.slack.slack_handlers.create_program_action",
            new_callable=AsyncMock,
        ) as mock_create_action,
        patch(
            "app.interfaces.slack.slack_handlers.create_program_success_blocks"
        ) as mock_create_blocks,
        patch("app.interfaces.slack.slack_handlers.ProgramRepository"),
        patch("app.interfaces.slack.slack_handlers.ProgramService"),
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
            "created com sucesso" in kwargs.get("text", "")
            or kwargs.get("blocks") is not None
        )


@pytest.mark.anyio
async def test_handle_create_program_no_name(mock_ack, mock_context):
    command = {"channel_id": "C123", "text": ""}

    await handle_create_program(mock_ack, command, mock_context)

    mock_ack.assert_awaited_once()
    mock_context.say.assert_awaited_once()
    args, kwargs = mock_context.say.call_args
    assert "forneça um nome" in args[0]


@pytest.mark.anyio
async def test_handle_create_program_error(mock_ack, mock_context):
    command = {"channel_id": "C123", "text": "New Program"}

    with (
        patch(
            "app.interfaces.slack.slack_handlers.create_program_action",
            new_callable=AsyncMock,
        ) as mock_create_action,
        patch("app.interfaces.slack.slack_handlers.ProgramRepository"),
        patch("app.interfaces.slack.slack_handlers.ProgramService"),
    ):
        mock_create_action.side_effect = Exception("Test Error")

        await handle_create_program(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_context.say.assert_awaited_once()
        args, _ = mock_context.say.call_args
        assert "Error on creating program" in args[0]


@pytest.mark.anyio
async def test_handle_list_programs_success(mock_ack, mock_context):
    command = {}

    with (
        patch(
            "app.interfaces.slack.slack_handlers.list_programs_action",
            new_callable=AsyncMock,
        ) as mock_list_action,
        patch(
            "app.interfaces.slack.slack_handlers.create_programs_list_blocks"
        ) as mock_list_blocks,
        patch("app.interfaces.slack.slack_handlers.ProgramRepository"),
        patch("app.interfaces.slack.slack_handlers.ProgramService"),
    ):
        mock_list_action.return_value = []
        mock_list_blocks.return_value = []

        await handle_list_programs(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_list_action.assert_awaited_once()
        mock_context.say.assert_awaited_once()


@pytest.mark.anyio
async def test_handle_list_programs_error(mock_ack, mock_context):
    command = {}

    with (
        patch(
            "app.interfaces.slack.slack_handlers.list_programs_action",
            new_callable=AsyncMock,
        ) as mock_list_action,
        patch("app.interfaces.slack.slack_handlers.ProgramRepository"),
        patch("app.interfaces.slack.slack_handlers.ProgramService"),
    ):
        mock_list_action.side_effect = Exception("List Error")

        await handle_list_programs(mock_ack, command, mock_context)

        mock_ack.assert_awaited_once()
        mock_context.say.assert_awaited_once()
        args, _ = mock_context.say.call_args
        assert "Error listing programs" in args[0]
