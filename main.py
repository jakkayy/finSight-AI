import logging
from db.database import init_db
from bot.telegram_bot import run_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    init_db()
    run_bot()
