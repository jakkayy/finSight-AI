import logging
import yfinance as yf
from telegram import Bot
from apscheduler.triggers.interval import IntervalTrigger
from db.database import SessionLocal
from db.models import User, Watchlist
from scheduler.jobs import scheduler
from config.settings import settings

logger = logging.getLogger(__name__)


def _get_price_change(symbol: str) -> tuple[float, float]:
    """Returns (current_price, change_pct)."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d")
    if len(hist) < 2:
        return 0.0, 0.0
    current = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2])
    change_pct = ((current - prev) / prev) * 100
    return current, round(change_pct, 2)


async def check_price_alerts():
    """Check all watchlist symbols and notify users when price threshold is breached."""
    bot = Bot(token=settings.telegram_bot_token)
    db = SessionLocal()
    try:
        entries = db.query(Watchlist).all()
        for entry in entries:
            try:
                current_price, change_pct = _get_price_change(entry.symbol)
                if abs(change_pct) >= entry.alert_threshold:
                    direction = "📈" if change_pct > 0 else "📉"
                    msg = (
                        f"{direction} *Alert: {entry.symbol}*\n"
                        f"ราคาเปลี่ยนแปลง *{change_pct:+.2f}%*\n"
                        f"ราคาปัจจุบัน: ${current_price:.2f}\n"
                        f"เกิน threshold ที่ตั้งไว้ ({entry.alert_threshold}%)"
                    )
                    await bot.send_message(
                        chat_id=entry.user.telegram_id,
                        text=msg,
                        parse_mode="Markdown",
                    )
            except Exception as e:
                logger.error("Alert check failed for %s: %s", entry.symbol, e)
    finally:
        db.close()


def register_alert_job():
    scheduler.add_job(
        check_price_alerts,
        trigger=IntervalTrigger(minutes=30),
        id="price_alerts",
        replace_existing=True,
    )
    logger.info("Price alert job registered — checks every 30 minutes")
