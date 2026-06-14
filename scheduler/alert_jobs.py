import logging
from datetime import datetime, timedelta, timezone
import yfinance as yf
from telegram import Bot
from apscheduler.triggers.interval import IntervalTrigger
from db.database import SessionLocal
from db.models import Watchlist
from scheduler.jobs import scheduler
from config.settings import settings

logger = logging.getLogger(__name__)

ALERT_COOLDOWN_HOURS = 4


def _get_price_change(symbol: str) -> tuple[float, float]:
    """Returns (current_price, change_pct)."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d")
    if len(hist) < 2:
        return 0.0, 0.0
    current = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2])
    return current, round(((current - prev) / prev) * 100, 2)


def _cooldown_passed(entry: Watchlist) -> bool:
    if entry.last_alerted_at is None:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ALERT_COOLDOWN_HOURS)
    last = entry.last_alerted_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last < cutoff


async def check_price_alerts():
    """Check watchlist symbols and notify users when threshold is breached (max once per 4h)."""
    bot = Bot(token=settings.telegram_bot_token)
    db = SessionLocal()
    try:
        entries = db.query(Watchlist).all()
        for entry in entries:
            try:
                current_price, change_pct = _get_price_change(entry.symbol)
                if abs(change_pct) < entry.alert_threshold:
                    continue
                if not _cooldown_passed(entry):
                    continue

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
                entry.last_alerted_at = datetime.now(timezone.utc)
                db.commit()

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
    logger.info("Price alert job registered — checks every 30 min, cooldown %dh", ALERT_COOLDOWN_HOURS)
