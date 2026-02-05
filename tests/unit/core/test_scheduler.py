from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.scheduler import monthly_job, start_scheduler, stop_scheduler


class TestMonthlyJob:
    @pytest.mark.anyio
    async def test_monthly_job_success(self):
        mock_session = AsyncMock()

        mock_cron_service = AsyncMock()
        mock_cron_service.run_monthly_job.return_value = {
            "cycle_reference": "2026-01",
            "close_cycle": {"success": []},
            "notify": {"success": []},
        }

        mock_async_session = MagicMock()
        mock_async_session.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_async_session.return_value.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.core.database.async_session", mock_async_session),
            patch("app.repositories.program_repository.ProgramRepository"),
            patch("app.repositories.achievement_repository.AchievementRepository"),
            patch("app.repositories.activity_repository.ActivityRepository"),
            patch("app.repositories.user_repository.UserRepository"),
            patch("app.services.achievement_service.AchievementService"),
            patch(
                "app.services.cron_service.CronService",
                return_value=mock_cron_service,
            ),
        ):
            await monthly_job()

            mock_cron_service.run_monthly_job.assert_called_once()

    @pytest.mark.anyio
    async def test_monthly_job_handles_exception(self):
        mock_session = AsyncMock()

        mock_cron_service = AsyncMock()
        mock_cron_service.run_monthly_job.side_effect = Exception("Database error")

        mock_async_session = MagicMock()
        mock_async_session.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_async_session.return_value.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.core.database.async_session", mock_async_session),
            patch("app.repositories.program_repository.ProgramRepository"),
            patch("app.repositories.achievement_repository.AchievementRepository"),
            patch("app.repositories.activity_repository.ActivityRepository"),
            patch("app.repositories.user_repository.UserRepository"),
            patch("app.services.achievement_service.AchievementService"),
            patch(
                "app.services.cron_service.CronService",
                return_value=mock_cron_service,
            ),
            patch("app.core.scheduler.logger") as mock_logger,
        ):
            await monthly_job()

            mock_logger.error.assert_called_once()


class TestStartScheduler:
    def test_start_scheduler_when_disabled(self):
        mock_settings = MagicMock()
        mock_settings.CRON_ENABLED = False

        with (
            patch("app.core.scheduler.settings", mock_settings),
            patch("app.core.scheduler.scheduler") as mock_scheduler,
            patch("app.core.scheduler.logger") as mock_logger,
        ):
            start_scheduler()

            mock_scheduler.add_job.assert_not_called()
            mock_scheduler.start.assert_not_called()
            mock_logger.info.assert_called_once_with(
                "Scheduler is disabled (CRON_ENABLED=False)"
            )

    def test_start_scheduler_when_enabled(self):
        """Test scheduler starts correctly when CRON_ENABLED is True."""
        mock_settings = MagicMock()
        mock_settings.CRON_ENABLED = True
        mock_settings.CRON_DAY = 1
        mock_settings.CRON_HOUR = 3
        mock_settings.CRON_MINUTE = 0

        with (
            patch("app.core.scheduler.settings", mock_settings),
            patch("app.core.scheduler.scheduler") as mock_scheduler,
            patch("app.core.scheduler.CronTrigger") as mock_trigger_class,
        ):
            mock_trigger = MagicMock()
            mock_trigger_class.return_value = mock_trigger

            start_scheduler()

            mock_trigger_class.assert_called_once_with(
                day=1,
                hour=3,
                minute=0,
                timezone="UTC",
            )
            mock_scheduler.add_job.assert_called_once_with(
                monthly_job,
                trigger=mock_trigger,
                id="monthly_close_cycle_job",
                name="Monthly Close Cycle and Notify",
                replace_existing=True,
            )
            mock_scheduler.start.assert_called_once()


class TestStopScheduler:
    def test_stop_scheduler_when_running(self):
        with (
            patch("app.core.scheduler.scheduler") as mock_scheduler,
            patch("app.core.scheduler.logger") as mock_logger,
        ):
            mock_scheduler.running = True

            stop_scheduler()

            mock_scheduler.shutdown.assert_called_once_with(wait=False)
            mock_logger.info.assert_called_once_with("Scheduler stopped")

    def test_stop_scheduler_when_not_running(self):
        with (
            patch("app.core.scheduler.scheduler") as mock_scheduler,
            patch("app.core.scheduler.logger") as mock_logger,
        ):
            mock_scheduler.running = False

            stop_scheduler()

            mock_scheduler.shutdown.assert_not_called()
            mock_logger.info.assert_not_called()
