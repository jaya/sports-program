from datetime import datetime


def is_within_allowed_window(date_to_check: datetime) -> bool:
    if date_to_check.tzinfo:
        now = datetime.now(date_to_check.tzinfo)
    else:
        now = datetime.now()

    current_month_total = (now.year * 12) + now.month
    check_month_total = (date_to_check.year * 12) + date_to_check.month

    diff = current_month_total - check_month_total

    return diff in (0, 1)
