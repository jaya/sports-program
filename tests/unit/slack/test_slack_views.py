from datetime import datetime
from unittest.mock import Mock

from app.interfaces.slack.slack_views import (
    create_program_success_blocks,
    create_programs_list_blocks,
)
from app.models.program import Program


class TestSlackBlocks:
    # --- Tests for create_program_success_blocks ---

    def test_success_block_handles_end_date_none(self):
        """Tests whether 'N/A' is rendered when end_date is None"""
        # Arrange
        start = datetime(2023, 1, 1)

        # Act
        blocks = create_program_success_blocks("JavaToPython", "C123", start, None)

        # Assert - Python allows "drill down" easily into the dictionary
        text_section = blocks[2]["text"]["text"]

        assert "Start Date: 01/01/2023" in text_section
        assert "End Date: N/A" in text_section

    def test_success_block_formats_dates_correctly(self):
        """Tests whether dates are formatted correctly"""
        start = datetime(2023, 10, 5)
        end = datetime(2023, 11, 5)

        blocks = create_program_success_blocks("Mentoria", "C123", start, end)

        text_section = blocks[2]["text"]["text"]
        assert "Start Date: 05/10/2023" in text_section
        assert "End Date: 05/11/2023" in text_section

    # --- Tests for create_programs_list_blocks ---

    def test_list_blocks_handles_multiple_items(self):
        """Tests whether the loop generates the correct number of blocks"""
        # Arrange: Creating Mocks of the Program object to not depend on the real model
        prog1 = Mock(spec=Program)
        prog1.name = "P1"
        prog1.slack_channel = "C1"
        prog1.start_date = datetime(2023, 1, 1)
        prog1.end_date = None

        prog2 = Mock(spec=Program)
        prog2.name = "P2"
        prog2.slack_channel = "C2"
        prog2.start_date = datetime(2023, 2, 1)
        prog2.end_date = datetime(2023, 2, 28)

        # Act
        blocks = create_programs_list_blocks([prog1, prog2])

        # Assert
        # Expected structure:
        # 0: Header, 1: Divider
        # 2: P1 Section, 3: Divider
        # 4: P2 Section, 5: Divider
        assert len(blocks) == 6
        assert "P1" in blocks[2]["text"]["text"]
        assert "P2" in blocks[4]["text"]["text"]

    def test_list_blocks_empty_returns_only_header(self):
        blocks = create_programs_list_blocks([])
        assert len(blocks) == 2  # Header and Divider
        assert blocks[0]["text"]["text"] == "Programs"
