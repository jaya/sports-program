from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time

from app.models.program import Program
from app.repositories.program_repository import ProgramRepository
from app.schemas.achievement import AchievementBatchResponse, NotifyResponse
from app.services.achievement_service import AchievementService
from app.services.cron_service import CronService, _get_previous_month_reference


@freeze_time("2026-03-15")
def test_get_previous_month_reference_regular_month():
    result = _get_previous_month_reference()
    assert result == "2026-02"


@freeze_time("2026-01-15")
def test_get_previous_month_reference_january_returns_december():
    result = _get_previous_month_reference()
    assert result == "2025-12"


@freeze_time("2026-12-01")
def test_get_previous_month_reference_december():
    result = _get_previous_month_reference()
    assert result == "2026-11"


@pytest.fixture
def mock_program_repo():
    return AsyncMock(spec=ProgramRepository)


@pytest.fixture
def mock_achievement_service():
    return AsyncMock(spec=AchievementService)


@pytest.fixture
def cron_service(mock_program_repo, mock_achievement_service):
    return CronService(
        program_repo=mock_program_repo,
        achievement_service=mock_achievement_service,
    )


@pytest.fixture
def sample_programs():
    return [
        Program(
            id=1,
            name="Program 1",
            slack_channel="C001",
            team_id="T001",
            start_date=datetime(2026, 1, 1),
        ),
        Program(
            id=2,
            name="Program 2",
            slack_channel="C002",
            team_id="T002",
            start_date=datetime(2026, 1, 1),
        ),
    ]


@pytest.mark.anyio
async def test_close_all_cycles_success(
    cron_service, mock_program_repo, mock_achievement_service, sample_programs
):
    mock_program_repo.find_active_in_cycle.return_value = sample_programs
    mock_achievement_service.close_cycle.return_value = AchievementBatchResponse(
        program_name="Program",
        cycle_reference="2026-01",
        total_created=2,
        users=["User1", "User2"],
    )

    result = await cron_service.close_all_cycles("2026-01")

    assert result["cycle_reference"] == "2026-01"
    assert result["total_programs"] == 2
    assert len(result["success"]) == 2
    assert len(result["errors"]) == 0
    assert result["success"][0]["achievements_created"] == 2


@pytest.mark.anyio
async def test_close_all_cycles_with_errors(
    cron_service, mock_program_repo, mock_achievement_service, sample_programs
):
    mock_program_repo.find_active_in_cycle.return_value = sample_programs
    mock_achievement_service.close_cycle.side_effect = [
        AchievementBatchResponse(
            program_name="Program 1",
            cycle_reference="2026-01",
            total_created=1,
            users=["User1"],
        ),
        Exception("Database error"),
    ]

    result = await cron_service.close_all_cycles("2026-01")

    assert len(result["success"]) == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["error"] == "Database error"


@pytest.mark.anyio
async def test_close_all_cycles_no_programs(
    cron_service, mock_program_repo, mock_achievement_service
):
    mock_program_repo.find_active_in_cycle.return_value = []

    result = await cron_service.close_all_cycles("2026-01")

    assert result["total_programs"] == 0
    assert len(result["success"]) == 0
    assert len(result["errors"]) == 0


@pytest.mark.anyio
@freeze_time("2026-02-15")
async def test_close_all_cycles_default_cycle_reference(
    cron_service, mock_program_repo, mock_achievement_service
):
    mock_program_repo.find_active_in_cycle.return_value = []

    result = await cron_service.close_all_cycles()

    assert result["cycle_reference"] == "2026-01"
    mock_program_repo.find_active_in_cycle.assert_called_once_with("2026-01")


@pytest.mark.anyio
async def test_close_all_cycles_null_result(
    cron_service, mock_program_repo, mock_achievement_service, sample_programs
):
    mock_program_repo.find_active_in_cycle.return_value = [sample_programs[0]]
    mock_achievement_service.close_cycle.return_value = None

    result = await cron_service.close_all_cycles("2026-01")

    assert len(result["success"]) == 1
    assert result["success"][0]["achievements_created"] == 0


@pytest.mark.anyio
async def test_notify_all_achievements_success(
    cron_service, mock_program_repo, mock_achievement_service, sample_programs
):
    mock_program_repo.find_active_in_cycle.return_value = sample_programs
    mock_achievement_service.notify_achievements.return_value = NotifyResponse(
        total_notified=3,
        message="Achievements notified successfully",
        users=["User1", "User2", "User3"],
    )

    result = await cron_service.notify_all_achievements("2026-01")

    assert result["cycle_reference"] == "2026-01"
    assert result["total_programs"] == 2
    assert len(result["success"]) == 2
    assert result["success"][0]["total_notified"] == 3


@pytest.mark.anyio
async def test_notify_all_achievements_with_errors(
    cron_service, mock_program_repo, mock_achievement_service, sample_programs
):
    mock_program_repo.find_active_in_cycle.return_value = sample_programs
    mock_achievement_service.notify_achievements.side_effect = [
        NotifyResponse(
            total_notified=1,
            message="Success",
            users=["User1"],
        ),
        Exception("Slack API error"),
    ]

    result = await cron_service.notify_all_achievements("2026-01")

    assert len(result["success"]) == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["error"] == "Slack API error"


@pytest.mark.anyio
@freeze_time("2026-02-15")
async def test_notify_all_achievements_default_cycle_reference(
    cron_service, mock_program_repo, mock_achievement_service
):
    mock_program_repo.find_active_in_cycle.return_value = []

    result = await cron_service.notify_all_achievements()

    assert result["cycle_reference"] == "2026-01"


@pytest.mark.anyio
async def test_run_monthly_job_success(
    cron_service, mock_program_repo, mock_achievement_service, sample_programs
):
    mock_program_repo.find_active_in_cycle.return_value = sample_programs
    mock_achievement_service.close_cycle.return_value = AchievementBatchResponse(
        program_name="Program",
        cycle_reference="2026-01",
        total_created=1,
        users=["User1"],
    )
    mock_achievement_service.notify_achievements.return_value = NotifyResponse(
        total_notified=1,
        message="Success",
        users=["User1"],
    )

    result = await cron_service.run_monthly_job("2026-01")

    assert result["cycle_reference"] == "2026-01"
    assert "close_cycle" in result
    assert "notify" in result
    assert result["close_cycle"]["total_programs"] == 2
    assert result["notify"]["total_programs"] == 2


@pytest.mark.anyio
@freeze_time("2026-02-15")
async def test_run_monthly_job_default_cycle_reference(
    cron_service, mock_program_repo, mock_achievement_service
):
    mock_program_repo.find_active_in_cycle.return_value = []

    result = await cron_service.run_monthly_job()

    assert result["cycle_reference"] == "2026-01"
