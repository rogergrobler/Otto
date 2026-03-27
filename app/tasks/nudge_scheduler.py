"""
Nudge Scheduler — APScheduler jobs that run nudge generators on a schedule.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.db.session import async_session as AsyncSessionLocal
from app.models.client import Client
from app.services.nudge_service import (
    generate_biomarker_due_nudge,
    generate_daily_checkin,
    generate_meal_reminder,
    generate_risk_flag,
    generate_training_prompt,
    generate_weekly_summary,
)

logger = logging.getLogger(__name__)


async def _run_for_all_clients(fn) -> None:
    """Execute a nudge generator for every active client."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Client).where(Client.is_active.is_(True)))
        clients = result.scalars().all()
        for client in clients:
            try:
                await fn(db, client)
            except Exception as exc:
                logger.error(f"Nudge error [{fn.__name__}] client={client.id}: {exc}")
        await db.commit()


async def job_morning_checkin() -> None:
    """07:00 UTC — daily check-in for every active client."""
    logger.info("Nudge job: morning check-in")
    await _run_for_all_clients(generate_daily_checkin)


async def job_meal_reminder() -> None:
    """13:00 UTC — meal reminder if fewer than 2 meals logged today."""
    logger.info("Nudge job: meal reminder")
    await _run_for_all_clients(generate_meal_reminder)


async def job_training_prompt() -> None:
    """18:00 UTC — training prompt if no Zone 2 in 2+ days."""
    logger.info("Nudge job: training prompt")
    await _run_for_all_clients(generate_training_prompt)


async def job_biomarker_due() -> None:
    """Daily 09:00 UTC — biomarker overdue check."""
    logger.info("Nudge job: biomarker due")
    await _run_for_all_clients(generate_biomarker_due_nudge)


async def job_weekly_summary() -> None:
    """Sunday 19:00 UTC — weekly summary."""
    logger.info("Nudge job: weekly summary")
    await _run_for_all_clients(generate_weekly_summary)


async def job_risk_flag() -> None:
    """Daily 10:00 UTC — risk flag check."""
    logger.info("Nudge job: risk flag")
    await _run_for_all_clients(generate_risk_flag)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(job_morning_checkin, CronTrigger(hour=7, minute=0))
    scheduler.add_job(job_meal_reminder, CronTrigger(hour=13, minute=0))
    scheduler.add_job(job_training_prompt, CronTrigger(hour=18, minute=0))
    scheduler.add_job(job_biomarker_due, CronTrigger(hour=9, minute=0))
    scheduler.add_job(job_weekly_summary, CronTrigger(day_of_week="sun", hour=19, minute=0))
    scheduler.add_job(job_risk_flag, CronTrigger(hour=10, minute=0))

    return scheduler
