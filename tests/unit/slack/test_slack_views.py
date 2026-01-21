from datetime import datetime
from unittest.mock import Mock

from app.core.config import settings
from app.interfaces.slack.slack_views import (
    activities_list_blocks,
    activity_registered_blocks,
    create_program_success_blocks,
    create_programs_list_blocks,
    error_blocks,
    help_blocks,
    invalid_date_blocks,
    invalid_reference_date_blocks,
)
from app.models.activity import Activity
from app.models.program import Program


def get_block_text(block):
    return block.get("text", {}).get("text", "")


def find_block_text_containing(blocks, substring):
    """
    Searches for a block that contains the given substring in its text.
    Returns the full text of the first matching block, or None if not found.
    """
    for block in blocks:
        text = get_block_text(block)
        if substring in text:
            return text
    return None


def create_mock_program(name="P1", channel="C1", start_date=None, end_date=None):
    mock_prog = Mock(spec=Program)
    mock_prog.name = name
    mock_prog.slack_channel = channel
    mock_prog.start_date = start_date or datetime(2023, 1, 1)
    mock_prog.end_date = end_date
    return mock_prog


def create_mock_activity(
    description="Activity",
    evidence_url=None,
    performed_at=None,
    created_at=None,
):
    mock_act = Mock(spec=Activity)
    mock_act.description = description
    mock_act.evidence_url = evidence_url
    mock_act.performed_at = performed_at or datetime(2023, 1, 1)
    mock_act.created_at = created_at or datetime(2023, 1, 1)
    return mock_act


class TestSlackBlocks:
    # --- Tests for create_program_success_blocks ---

    def test_success_block_handles_end_date_none(self):
        """Tests whether 'N/A' is rendered when end_date is None"""
        # Arrange
        start = datetime(2023, 1, 1)

        # Act
        blocks = create_program_success_blocks("JavaToPython", "C123", start, None)

        # Assert
        text_section = find_block_text_containing(blocks, "Start Date")
        assert text_section is not None
        assert "Start Date: 01/01/2023" in text_section
        assert "End Date: N/A" in text_section

    def test_success_block_formats_dates_correctly(self):
        """Tests whether dates are formatted correctly"""
        start = datetime(2023, 10, 5)
        end = datetime(2023, 11, 5)

        blocks = create_program_success_blocks("Mentoria", "C123", start, end)

        text_section = find_block_text_containing(blocks, "Start Date")
        assert text_section is not None
        assert "Start Date: 05/10/2023" in text_section
        assert "End Date: 05/11/2023" in text_section

    # --- Tests for create_programs_list_blocks ---

    def test_list_blocks_handles_multiple_items(self):
        """Tests whether the loop generates the correct number of blocks"""
        # Arrange
        prog1 = create_mock_program(
            name="P1", channel="C1", start_date=datetime(2023, 1, 1), end_date=None
        )
        prog2 = create_mock_program(
            name="P2",
            channel="C2",
            start_date=datetime(2023, 2, 1),
            end_date=datetime(2023, 2, 28),
        )

        # Act
        blocks = create_programs_list_blocks([prog1, prog2])

        # Assert
        # Check structure generally exists
        assert len(blocks) >= 2

        # Check content exists anywhere nicely
        assert find_block_text_containing(blocks, "P1") is not None
        assert find_block_text_containing(blocks, "P2") is not None

    def test_list_blocks_empty_returns_only_header(self):
        blocks = create_programs_list_blocks([])
        assert find_block_text_containing(blocks, "Programs") is not None

    # --- Tests for activity_registered_blocks ---

    def test_activity_registered_blocks_renders_correctly(self):
        """Tests content of activity registered blocks"""
        description = "Running 5km"
        date_str = "13/01/2026"
        count = 5

        blocks = activity_registered_blocks(description, date_str, count)

        assert find_block_text_containing(blocks, "Activity registered!") is not None

        count_block = find_block_text_containing(blocks, str(count))
        assert count_block is not None

        details_block = find_block_text_containing(blocks, description)
        assert details_block is not None
        assert date_str in details_block

    # --- Tests for invalid_date_blocks ---

    def test_invalid_date_blocks_content(self):
        """Tests content of invalid date blocks"""
        blocks = invalid_date_blocks()
        assert find_block_text_containing(blocks, "Invalid date!") is not None
        assert find_block_text_containing(blocks, "@DD/MM") is not None

    # --- Tests for invalid_reference_date_blocks ---

    def test_invalid_reference_date_blocks_content(self):
        """Tests content of invalid reference date blocks"""
        blocks = invalid_reference_date_blocks()
        assert find_block_text_containing(blocks, "Invalid reference date!") is not None
        assert find_block_text_containing(blocks, "@MM/YYYY") is not None

    # --- Tests for error_blocks ---

    def test_error_blocks_renders_message(self):
        """Tests that error blocks include the provided message"""
        msg = "Something went wrong"
        blocks = error_blocks(msg)
        assert find_block_text_containing(blocks, "Error ocurred!") is not None
        assert find_block_text_containing(blocks, msg) is not None

    # --- Tests for activities_list_blocks ---

    def test_activities_list_blocks_renders_activities(self):
        """Tests rendering of a list of activities"""
        # Arrange
        act1 = create_mock_activity(
            description="Yoga",
            evidence_url="http://evidence.com/1",
            performed_at=datetime(2023, 5, 20),
            created_at=datetime(2023, 5, 21),
        )

        act2 = create_mock_activity(
            description="Gym",
            evidence_url=None,
            performed_at=datetime(2023, 6, 12),
            created_at=datetime(2023, 6, 12),
        )

        # Act
        blocks = activities_list_blocks([act1, act2])

        # Assert
        count_text = find_block_text_containing(blocks, "Number of activities recorded")
        assert count_text is not None
        assert "2" in count_text

        # Check Activity 1 content
        act1_text = find_block_text_containing(blocks, "Yoga")
        assert act1_text is not None
        assert "http://evidence.com/1" in act1_text
        assert "20/05/2023" in act1_text  # Performed
        assert "21/05/2023" in act1_text  # Created

        # Check Activity 2 content
        act2_text = find_block_text_containing(blocks, "Gym")
        assert act2_text is not None
        assert "link" not in act2_text  # No evidence
        assert "12/06/2023" in act2_text

    def test_activities_list_blocks_empty(self):
        """Tests rendering with empty activity list"""
        blocks = activities_list_blocks([])

        count_text = find_block_text_containing(blocks, "Number of activities recorded")
        assert count_text is not None
        assert "0" in count_text

    # --- Tests for help_blocks ---

    def test_help_blocks_content(self):
        """Tests content of help blocks"""
        blocks = help_blocks()

        # Check for introduction
        assert find_block_text_containing(blocks, f"{settings.BOT_NAME}") is not None

        # Check for sections
        assert find_block_text_containing(blocks, "Prerequisites") is not None
        assert (
            find_block_text_containing(blocks, "Create and List Programs") is not None
        )
        assert find_block_text_containing(blocks, "Log an Activity") is not None
        assert find_block_text_containing(blocks, "Track Progress") is not None

        # Check for command examples
        assert find_block_text_containing(blocks, "/create-program") is not None
        assert find_block_text_containing(blocks, "/list-programs") is not None
        assert find_block_text_containing(blocks, "/list-activities") is not None
