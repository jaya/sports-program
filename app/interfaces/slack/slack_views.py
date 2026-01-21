from datetime import datetime

from app.models.activity import Activity
from app.models.program import Program


def create_program_success_blocks(
    program_name: str,
    slack_channel: str,
    start_date: datetime,
    end_date: datetime | None,
) -> list[dict]:
    p_start_date = start_date.strftime("%d/%m/%Y")
    p_end_date = "N/A"
    if end_date:
        p_end_date = end_date.strftime("%d/%m/%Y")

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Program created successfully!",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{program_name}*\n"
                    f":hash: Channel: <#{slack_channel}>\n"
                    f":calendar: Start Date: {p_start_date}\n"
                    f":checkered_flag: End Date: {p_end_date}"
                ),
            },
        },
    ]


def create_programs_list_blocks(programs: list[Program]) -> list[dict]:
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Programs", "emoji": True},
        },
        {"type": "divider"},
    ]
    for program in programs:
        start_date = program.start_date.strftime("%d/%m/%Y")
        end_date = program.end_date.strftime("%d/%m/%Y") if program.end_date else "N/A"
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{program.name}*\n"
                        f":hash: Channel: <#{program.slack_channel}>\n"
                        f":calendar: Start Date: {start_date}\n"
                        f":checkered_flag: End Date: {end_date}"
                    ),
                },
            }
        )
        blocks.append({"type": "divider"})
    return blocks


def activity_registered_blocks(
    description: str, activity_date: str, count_month: int
) -> list[dict]:
    """
    Build blocks for successful activity registration message.
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":white_check_mark: Activity registered!",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":checkered_flag: *Number of activities recorded in this cycle:* "
                    f"{count_month}"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":memo: *Description:* {description}\n"
                    f":calendar: *Date:* {activity_date}\n"
                ),
            },
        },
    ]


def invalid_date_blocks() -> list[dict]:
    """
    Build blocks for invalid date error message.
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":x: Invalid date!",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Please use the format `@DD/MM` with a valid date.\n"
                    ":bulb: Example: `@13/01` for January 13th."
                ),
            },
        },
    ]


def invalid_reference_date_blocks() -> list[dict]:
    """
    Build blocks for invalid reference date error message.
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":x: Invalid reference date!",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Please use the format `@MM/YYYY` with a valid date.\n"
                    ":bulb: Example: `@01/2024` for January 2024."
                ),
            },
        },
    ]


def error_blocks(message: str) -> list[dict]:
    """
    Build blocks for generic error messages.
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":warning: Error ocurred!",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"Was not possible to complete the operation.\n\n"
                    f":information_source: *Details:* {message}"
                ),
            },
        },
    ]


def activities_list_blocks(activities: list[Activity]) -> list[dict]:
    """
    Build blocks for a list of activities.
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Activities List",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":checkered_flag: *Number of activities recorded in this cycle:* "
                    f"{len(activities)}"
                ),
            },
        },
        {"type": "divider"},
    ]

    for activity in activities:
        evidence_text = ""
        if activity.evidence_url:
            evidence_text = f"\n:link: *Evidence:* <{activity.evidence_url}| link>"

        performed_date = activity.performed_at.strftime("%d/%m/%Y")
        created_date = activity.created_at.strftime("%d/%m/%Y")

        blocks.extend(
            [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f":memo: *Description:* {activity.description}\n"
                            f"{evidence_text}\n"
                            f":calendar: *Performed:* {performed_date}\n"
                            f":clock1: *Registered:* {created_date}"
                        ),
                    },
                },
                {"type": "divider"},
            ]
        )

    return blocks


def help_blocks():
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Hi there :wave: I'm the Sports Program Bot. I'm here to help you "
                    "manage programs and log your physical activities."
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Prerequisites*\n"
                    "To start using me, *add me to a channel* "
                    "and I'll introduce myself. I'm usually added to a team or project "
                    "channel. Type `/invite @SportsProgramBot` from the channel "
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Here are the main ways to interact with me:\n",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*:one: Create and List Programs*\nUse the `/create-program <name>`"
                    " command to create a new incentive program.\nUse `/list-programs`"
                    " to view all currently active programs.\n\n"
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*:two: Log an Activity*\nTo log what you've done, simply mention "
                    "me in a message with the description."
                    "\n\n:calendar: *Dates*: By default, it logs for *today*. "
                    "To log for a specific date, use the `@DD/MM` format."
                    "\n\nExample: `@SportsBot 5km run @20/01` (logs for Jan 20th)"
                    "\n:camera_with_flash: _Tip: If you attach a "
                    "photo to the message, it will be saved as evidence!\n\n"
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*:three: Track Progress*\nUse the `/list-activities` command "
                    "to see the list of logged activities."
                    "\n\n:calendar: *Filtering*: By default, it shows the "
                    "*current month*. To view a past month, use the `@MM/YYYY` "
                    "format."
                    "\n\nExample: `/list-activities @12/2025`\n\n"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        ":eyes: Questions? "
                        "Type *help* at any time to see a summary of commands."
                    ),
                }
            ],
        },
    ]
