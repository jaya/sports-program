import re
from datetime import date


def parse_activity_date(text: str) -> tuple[str, str | None]:
    """
    Parses natural language text to extract a date in @DD/MM format and a description.
    Cleans up Slack mentions and extra whitespace.
    """
    # Pattern to match @DD/MM format
    date_pattern = r"@(\d{1,2})/(\d{1,2})"
    match = re.search(date_pattern, text)

    # Clean up description first (remove date pattern and bot mention)
    description = re.sub(date_pattern, "", text).strip()
    description = re.sub(r"<@[A-Z0-9]+>", "", description).strip()
    description = re.sub(r"\s+", " ", description)

    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        try:
            # Assuming current year for the date
            activity_date = date(date.today().year, month, day)
            return description, activity_date.isoformat()
        except ValueError:
            return description, None
    else:
        activity_date = date.today()
        return description, activity_date.isoformat()


def parse_reference_date(text: str) -> str | None:
    date_pattern = r"@(\d{1,2})/(\d{1,4})"
    match = re.search(date_pattern, text)
    if match:
        month = int(match.group(1))
        year = int(match.group(2))
        return date(year, month, 1).strftime("%Y-%m")
    return None
