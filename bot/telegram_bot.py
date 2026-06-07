import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from agents.technical_agent import analyze_technical
from config.settings import settings

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ยินดีต้อนรับสู่ *FinSight* 📊\n\n"
        "คำสั่งที่ใช้ได้:\n"
        "/analyze `<symbol>` — วิเคราะห์ technical\n"
        "/add `<symbol>` — เพิ่มใน watchlist\n"
        "/remove `<symbol>` — ลบจาก watchlist\n"
        "/list — ดู watchlist ของคุณ\n"
        "/help — ความช่วยเหลือ",
        parse_mode="Markdown",
    )


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("กรุณาระบุ symbol เช่น /analyze AAPL")
        return

    symbol = context.args[0].upper()
    msg = await update.message.reply_text(f"🔍 กำลังวิเคราะห์ {symbol}...")

    try:
        result = analyze_technical(symbol)
        await msg.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error("Technical analysis failed for %s: %s", symbol, e)
        await msg.edit_text(f"❌ เกิดข้อผิดพลาด: {e}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*FinSight — Multi-Agent Investment Research*\n\n"
        "/analyze `<symbol>` — วิเคราะห์หุ้น/crypto แบบ technical\n"
        "/add `<symbol>` — เพิ่มหุ้นใน watchlist\n"
        "/remove `<symbol>` — ลบหุ้นจาก watchlist\n"
        "/list — แสดง watchlist\n"
        "/alert `<symbol>` `<threshold%>` — ตั้ง alert เช่น /alert AAPL 5\n\n"
        "ตัวอย่าง: /analyze NVDA หรือ /analyze BTC-USD",
        parse_mode="Markdown",
    )


def run_bot():
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("help", cmd_help))

    logger.info("FinSight bot started")
    app.run_polling(drop_pending_updates=True)
