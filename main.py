from utils.logger import setup_logging
from db.database import init_db
from scheduler.jobs import start_scheduler
from scheduler.alert_jobs import register_alert_job
from bot.telegram_bot import run_bot

if __name__ == "__main__":
    setup_logging()
    init_db()
    start_scheduler()
    register_alert_job()
    run_bot()
