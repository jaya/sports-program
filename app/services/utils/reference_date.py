from dataclasses import dataclass
from app.exceptions.business import BusinessRuleViolationError


@dataclass
class ReferenceDate:
    year: int
    month: int

    @classmethod
    def from_str(cls, date_str: str) -> "ReferenceDate":
        try:
            if not date_str or "-" not in date_str:
                raise ValueError

            year_part, month_part = date_str.split("-")
            year = int(year_part)
            month = int(month_part)

            if not (1 <= month <= 12):
                raise ValueError

            return cls(year=year, month=month)
        except (ValueError, AttributeError):
            raise BusinessRuleViolationError(
                "The date format must be YYYY-MM."
            )
