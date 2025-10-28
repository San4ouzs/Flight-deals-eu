from __future__ import annotations
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from .storage import ensure_db, select_deals

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # можно не ограничивать, если хочется

async def deals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        threshold = float(args[0]) if len(args) >= 1 else -20.0
        limit = int(args[1]) if len(args) >= 2 else 50
    except Exception:
        await update.message.reply_text("Использование: /deals <порог %> <лимит>. Пример: /deals -20 50")
        return

    engine = ensure_db()
    rows = select_deals(engine, threshold_pct=threshold, limit=limit)
    if not rows:
        await update.message.reply_text("Сделок не найдено.")
        return
    lines = ["FROM  TO   DATE        PRICE  AVG365  %vsAVG  PROVIDER"]
    for r in rows:
        lines.append(f"{r['origin']:4} {r['destination']:4} {r['dep_date']}  {r['price']:.0f}  {r['avg365']:.0f}  {r['pct_vs_avg']:.1f}%  {r['provider']}")
    msg = "\n".join(lines[:80])
    await update.message.reply_text(f"\u2705 Текущие сделки (порог {threshold}%):\n\n{msg}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Команда: /deals -20 50 — показать направления дешевле средней на 20% (лимит 50)")

def main():
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN не задан в .env")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deals", deals_cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
