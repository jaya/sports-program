import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

logger = structlog.get_logger()

scheduler = AsyncIOScheduler()


async def monthly_job():
    from app.core.database import async_session
    from app.repositories.program_repository import ProgramRepository
    from app.services.achievement_service import AchievementService
    from app.services.cron_service import CronService

    logger.info("Monthly job triggered by scheduler")

    async with async_session() as session:
        program_repo = ProgramRepository(session)

        from app.repositories.achievement_repository import AchievementRepository
        from app.repositories.activity_repository import ActivityRepository
        from app.repositories.user_repository import UserRepository

        achievement_repo = AchievementRepository(session)
        activity_repo = ActivityRepository(session)
        user_repo = UserRepository(session)

        achievement_service = AchievementService(
            db=session,
            achievement_repo=achievement_repo,
            user_repo=user_repo,
            program_repo=program_repo,
            activity_repo=activity_repo,
        )

        cron_service = CronService(
            program_repo=program_repo,
            achievement_service=achievement_service,
        )

        try:
            result = await cron_service.run_monthly_job()
            logger.info(f"Monthly job completed successfully: {result}")
        except Exception as e:
            logger.error(f"Monthly job failed: {e}", e)


def start_scheduler():
    if not settings.CRON_ENABLED:
        logger.info("Scheduler is disabled (CRON_ENABLED=False)")
        return

    trigger = CronTrigger(
        day=settings.CRON_DAY,
        hour=settings.CRON_HOUR,
        minute=settings.CRON_MINUTE,
        timezone="UTC",
    )

    scheduler.add_job(
        monthly_job,
        trigger=trigger,
        id="monthly_close_cycle_job",
        name="Monthly Close Cycle and Notify",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started. Monthly job scheduled for day {settings.CRON_DAY} "
        f"at {settings.CRON_HOUR:02d}:{settings.CRON_MINUTE:02d} UTC"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
