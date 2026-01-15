from datetime import datetime

from app.models.activity import Activity


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
                "text": "Programa criado com sucesso!",
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
                    f":hash: Canal: <#{slack_channel}>\n"
                    f":calendar: Início: {p_start_date}\n"
                    f":checkered_flag: Fim: {p_end_date}"
                ),
            },
        },
    ]


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
                    f":checkered_flag: Number of activities recorded in this cycle: "
                    f"*{count_month}*"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":memo: Description: {description}\n"
                    f":calendar: Date: {activity_date}\n"
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
                    f":checkered_flag: Number of activities recorded in this cycle: "
                    f"*{len(activities)}*"
                ),
            },
        },
        {"type": "divider"},
    ]

    for activity in activities:
        evidence_text = ""
        if activity.evidence_url:
            evidence_text = f"\n:link: <{activity.evidence_url}| Evidence>"

        performed_date = activity.performed_at.strftime("%d/%m/%Y")
        created_date = activity.created_at.strftime("%d/%m/%Y")

        blocks.extend(
            [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{activity.description}* {evidence_text}\n"
                            f":calendar: Performed: {performed_date}\n"
                            f":clock1: Registered: {created_date}"
                        ),
                    },
                },
                {"type": "divider"},
            ]
        )

    return blocks
