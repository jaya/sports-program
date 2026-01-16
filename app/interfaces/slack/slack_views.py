from datetime import datetime

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
                "text": "Program successfully created!",
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
                    f":calendar: Start: {p_start_date}\n"
                    f":checkered_flag: End: {p_end_date}"
                ),
            },
        },
    ]


def create_programs_list_blocks(programs: list[Program]) -> list[dict]:
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Programas", "emoji": True},
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
                        f":calendar: Start: {start_date}\n"
                        f":checkered_flag: End: {end_date}"
                    ),
                },
            }
        )
        blocks.append({"type": "divider"})
    return blocks
