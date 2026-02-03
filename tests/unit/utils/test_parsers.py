from freezegun import freeze_time

from app.utils.parsers import parse_activity_date, parse_reference_date


class TestParseActivityDate:

    @freeze_time("2026-03-15")
    def test_parse_date_same_month(self):
        description, activity_date = parse_activity_date("Morning run @10/03")
        assert description == "Morning run"
        assert activity_date == "2026-03-10"

    @freeze_time("2026-03-15")
    def test_parse_date_previous_month(self):
        description, activity_date = parse_activity_date("Evening walk @25/02")
        assert description == "Evening walk"
        assert activity_date == "2026-02-25"

    @freeze_time("2026-01-15")
    def test_parse_date_december_in_january(self):
        description, activity_date = parse_activity_date("New Year run @31/12")
        assert description == "New Year run"
        assert activity_date == "2025-12-31"

    @freeze_time("2026-02-10")
    def test_parse_date_december_in_february(self):
        description, activity_date = parse_activity_date(
            "Late submission @15/12")
        assert description == "Late submission"
        assert activity_date == "2025-12-15"

    @freeze_time("2026-06-15")
    def test_parse_date_future_month_assumed_previous_year(self):
        description, activity_date = parse_activity_date("Summer run @10/08")
        assert description == "Summer run"
        assert activity_date == "2025-08-10"

    @freeze_time("2026-03-15")
    def test_parse_date_no_date_returns_today(self):
        description, activity_date = parse_activity_date(
            "Morning run without date")
        assert description == "Morning run without date"
        assert activity_date == "2026-03-15"

    @freeze_time("2026-03-15")
    def test_parse_date_invalid_date_returns_none(self):
        description, activity_date = parse_activity_date("Invalid @31/02")
        assert description == "Invalid"
        assert activity_date is None

    @freeze_time("2026-03-15")
    def test_parse_date_cleans_slack_mention(self):
        description, activity_date = parse_activity_date(
            "<@U123ABC> Morning run @10/03"
        )
        assert description == "Morning run"
        assert activity_date == "2026-03-10"

    @freeze_time("2026-03-15")
    def test_parse_date_cleans_extra_whitespace(self):
        description, activity_date = parse_activity_date(
            "Morning   run   with   spaces @10/03"
        )
        assert description == "Morning run with spaces"
        assert activity_date == "2026-03-10"

    @freeze_time("2026-03-15")
    def test_parse_date_single_digit_day_and_month(self):
        description, activity_date = parse_activity_date("Quick run @5/3")
        assert description == "Quick run"
        assert activity_date == "2026-03-05"


class TestParseReferenceDate:

    def test_parse_reference_date_valid(self):
        result = parse_reference_date("@03/2026")
        assert result == "2026-03"

    def test_parse_reference_date_short_year(self):
        result = parse_reference_date("@12/26")
        assert result == "0026-12"

    def test_parse_reference_date_no_match(self):
        result = parse_reference_date("no date here")
        assert result is None

    def test_parse_reference_date_single_digit_month(self):
        result = parse_reference_date("@1/2026")
        assert result == "2026-01"
