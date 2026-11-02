import os
import uuid
import random
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from supabase import create_client, Client

# راه‌اندازی یک وب‌سرور کوچک برای پاسخ به درخواست‌های هاست (پورت 7860)
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "🤖 Telegram Bot & Minesweeper Duel Server is Live!"

def run_web():
    app_web.run(host="0.0.0.0", port=7860)

# اطلاعات سوپابیس و تلگرام
SUPABASE_URL = "https://hpxxnwzkzvryuzmizbeg.supabase.co"
SUPABASE_KEY = "Sb_publishable_qi_8yuTxTJ_6wICbVFIG7w_VlLHl0j8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

WEB_APP_URL = "https://arshiaeliasy.github.io/minesweeper-duel/"
BOT_TOKEN = "9199489345:AAE8KGBymljPmHR-NJdRVyPkU4NbMMzF7s0"

async def start_duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    match_id = f"duel_{uuid.uuid4().hex[:8]}"

    board = []
    mine_positions = random.sample(range(36), 6)
    for i in range(36):
        board.append({
            "revealed": False,
            "mine": i in mine_positions,
            "value": 1 if i in mine_positions else 0
        })

    supabase.table("duels").insert({
        "match_id": match_id,
        "player1_name": user.first_name,
        "player1_id": user.id,
        "status": "waiting",
        "turn": user.id,
        "board_state": board
    }).execute()

    keyboard = [
        [InlineKeyboardButton("⚔️ پیوستن به دوئل مین‌روب", callback_data=f"join_{match_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎮 **مسابقه دوئل مین‌روب!**\n\n"
        f"👤 آغازگر: {user.first_name}\n"
        f"کی جرات داره این چالش رو قبول کنه؟ 😎",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def join_duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    match_id = query.data.replace("join_", "")

    res = supabase.table("duels").select("*").eq("match_id", match_id).execute()
    if not res.data:
        await query.edit_message_text("❌ این مسابقه منقضی شده یا وجود ندارد.")
        return

    game = res.data[0]

    if game["status"] != "waiting":
        await query.edit_message_text("⚠️ این بازی قبلاً شروع شده است!")
        return

    if game["player1_id"] == user.id:
        await query.answer("شما نمی‌توانید با خودتان بازی کنید! منتظر حریف بمانید.", show_alert=True)
        return

    supabase.table("duels").update({
        "player2_name": user.first_name,
        "player2_id": user.id,
        "status": "playing"
    }).eq("match_id", match_id).execute()

    final_url = f"{WEB_APP_URL}?match={match_id}"
    keyboard = [
        [InlineKeyboardButton("🚀 ورود به زمین مسابقه", url=final_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"🔥 **دوئل شکل گرفت و آماده است!**\n\n"
        f"👤 بازیکن اول: {game['player1_name']}\n"
        f"👤 بازیکن دوم: {user.first_name}\n\n"
        f"برای شروع بازی روی دکمه زیر بزنید:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def main():
    # اجرای وب‌سرور در پس‌زمینه برای راضی نگه داشتن هاست
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    # راه‌اندازی ربات تلگرام
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("duel", start_duel))
    app.add_handler(CallbackQueryHandler(join_duel, pattern="^join_"))

    print("🤖 ربات با موفقیت روی هاست ابری Hugging Face روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
