import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from db.database import SessionLocal
from db.models import User, Watchlist
from agents.orchestrator import run_full_analysis
from config.settings import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Bangkok")


async def morning_briefing():
    """Send daily morning briefing to all users with their watchlist."""
    bot = Bot(token=settings.telegram_bot_token)
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            symbols = [w.symbol for w in user.watchlist]
            if not symbols:
                continue

            header = "☀️ *FinSight Morning Briefing*\n\n"
            await bot.send_message(chat_id=user.telegram_id, text=header, parse_mode="Markdown")

            for symbol in symbols:
                try:
                    report = run_full_analysis(symbol)
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=report,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logger.error("Failed to analyze %s for user %s: %s", symbol, user.telegram_id, e)
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        morning_briefing,
        trigger=CronTrigger(hour=8, minute=0, timezone="Asia/Bangkok"),
        id="morning_briefing",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — morning briefing at 08:00 Asia/Bangkok")


def stop_scheduler():
    scheduler.shutdown()
