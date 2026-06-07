import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy.exc import IntegrityError
from agents.technical_agent import analyze_technical
from agents.orchestrator import run_full_analysis
from db.database import SessionLocal
from db.models import User, Watchlist
from config.settings import settings

logger = logging.getLogger(__name__)


def _get_or_create_user(db, telegram_id: str, username: str | None) -> User:
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        _get_or_create_user(
            db,
            str(update.effective_user.id),
            update.effective_user.username,
        )
    finally:
        db.close()

    await update.message.reply_text(
        "ยินดีต้อนรับสู่ *FinSight* 📊\n\n"
        "คำสั่งที่ใช้ได้:\n"
        "/analyze `<symbol>` — วิเคราะห์ technical\n"
        "/report `<symbol>` — รายงานเต็ม (Technical+News+Sentiment)\n"
        "/add `<symbol>` — เพิ่มใน watchlist\n"
        "/remove `<symbol>` — ลบจาก watchlist\n"
        "/list — ดู watchlist\n"
        "/alert `<symbol>` `<threshold%>` — ตั้ง alert\n"
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


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("กรุณาระบุ symbol เช่น /report NVDA")
        return

    symbol = context.args[0].upper()
    msg = await update.message.reply_text(f"🤖 กำลังสร้าง full report สำหรับ {symbol}...\n(อาจใช้เวลา 1-2 นาที)")

    try:
        report = run_full_analysis(symbol)
        await msg.edit_text(report, parse_mode="Markdown")
    except Exception as e:
        logger.error("Full report failed for %s: %s", symbol, e)
        await msg.edit_text(f"❌ เกิดข้อผิดพลาด: {e}")


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("กรุณาระบุ symbol เช่น /add AAPL")
        return

    symbol = context.args[0].upper()
    db = SessionLocal()
    try:
        user = _get_or_create_user(db, str(update.effective_user.id), update.effective_user.username)
        entry = Watchlist(user_id=user.id, symbol=symbol)
        db.add(entry)
        db.commit()
        await update.message.reply_text(f"✅ เพิ่ม *{symbol}* ใน watchlist แล้ว", parse_mode="Markdown")
    except IntegrityError:
        db.rollback()
        await update.message.reply_text(f"*{symbol}* อยู่ใน watchlist แล้ว", parse_mode="Markdown")
    except Exception as e:
        db.rollback()
        await update.message.reply_text(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        db.close()


async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("กรุณาระบุ symbol เช่น /remove AAPL")
        return

    symbol = context.args[0].upper()
    db = SessionLocal()
    try:
        user = _get_or_create_user(db, str(update.effective_user.id), update.effective_user.username)
        entry = db.query(Watchlist).filter_by(user_id=user.id, symbol=symbol).first()
        if entry:
            db.delete(entry)
            db.commit()
            await update.message.reply_text(f"🗑 ลบ *{symbol}* ออกจาก watchlist แล้ว", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"ไม่พบ *{symbol}* ใน watchlist", parse_mode="Markdown")
    finally:
        db.close()


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        user = _get_or_create_user(db, str(update.effective_user.id), update.effective_user.username)
        if not user.watchlist:
            await update.message.reply_text("Watchlist ยังว่างอยู่ ใช้ /add เพิ่มหุ้นได้เลย")
            return

        lines = ["📋 *Watchlist ของคุณ*\n"]
        for w in user.watchlist:
            lines.append(f"• `{w.symbol}` — alert เมื่อเปลี่ยน {w.alert_threshold}%")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


async def cmd_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("ใช้งาน: /alert AAPL 5 (แจ้งเตือนเมื่อราคาเปลี่ยน 5%)")
        return

    symbol = context.args[0].upper()
    try:
        threshold = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Threshold ต้องเป็นตัวเลข เช่น /alert AAPL 5")
        return

    db = SessionLocal()
    try:
        user = _get_or_create_user(db, str(update.effective_user.id), update.effective_user.username)
        entry = db.query(Watchlist).filter_by(user_id=user.id, symbol=symbol).first()
        if not entry:
            await update.message.reply_text(f"ไม่พบ *{symbol}* ใน watchlist กรุณา /add ก่อน", parse_mode="Markdown")
            return
        entry.alert_threshold = threshold
        db.commit()
        await update.message.reply_text(
            f"🔔 ตั้ง alert *{symbol}* ที่ {threshold}% แล้ว", parse_mode="Markdown"
        )
    finally:
        db.close()


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*FinSight — Multi-Agent Investment Research*\n\n"
        "/analyze `<symbol>` — Technical analysis\n"
        "/report `<symbol>` — Full report (Technical+News+Sentiment)\n"
        "/add `<symbol>` — เพิ่มใน watchlist\n"
        "/remove `<symbol>` — ลบจาก watchlist\n"
        "/list — แสดง watchlist\n"
        "/alert `<symbol>` `<n>` — ตั้ง alert ที่ n%\n\n"
        "ตัวอย่าง: /report NVDA หรือ /alert BTC-USD 3",
        parse_mode="Markdown",
    )


def run_bot():
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("alert", cmd_alert))
    app.add_handler(CommandHandler("help", cmd_help))

    logger.info("FinSight bot started")
    app.run_polling(drop_pending_updates=True)
