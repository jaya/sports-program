from datetime import datetime


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
                "text": f"*{program_name}*\n:hash: Canal: <#{slack_channel}>\n:calendar: Início: {p_start_date}\n:checkered_flag: Fim: {p_end_date}",
            },
        },
    ]
