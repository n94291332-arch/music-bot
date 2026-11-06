import os
import threading
import requests

from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
music_files = {}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Music Bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

async def start(update, context):
    await update.message.reply_text(
        "🎵 Музыка бот!\n"
        "Ырдын атын жаз же MP3 файл жөнөт."
    )

async def search_music(update, context):
    song = update.message.text
    await update.message.reply_text("🔎 Изделүүдө...")

    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": song, "entity": "song", "limit": 5},
            timeout=20
        )
        data = r.json()

        if not data["results"]:
            await update.message.reply_text("Ыр табылган жок.")
            return

        for item in data["results"]:
            title = item.get("trackName", "Музыка")
            artist = item.get("artistName", "Белгисиз")
            audio = item.get("previewUrl")

            if audio:
                keyboard = [[
                    InlineKeyboardButton("▶️ Угуу", url=audio),
                    InlineKeyboardButton("⬇️ Үзүндү", url=audio)
                ]]

                await update.message.reply_text(
                    f"🎵 {title}\n👤 {artist}\n\n"
                    "Бул каталогдогу кыска үзүндү.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

    except Exception as e:
        print(e)
        await update.message.reply_text("Издөөдө ката чыкты.")

async def upload_music(update, context):
    msg = update.message

    if msg.audio:
        file_id = msg.audio.file_id
        title = msg.audio.title or msg.audio.file_name or "Музыка"
        artist = msg.audio.performer or "Белгисиз"

    elif msg.document and msg.document.mime_type:
        if not msg.document.mime_type.startswith("audio/"):
            await msg.reply_text("Аудио файл жөнөт.")
            return
        file_id = msg.document.file_id
        title = msg.document.file_name or "Музыка"
        artist = "Белгисиз"

    else:
        return

    music_files[title.lower()] = file_id

    await msg.reply_text(
        f"✅ {title}\n👤 {artist}\n"
        "Музыка кабыл алынды!"
    )

async def play_music(update, context):
    query = update.callback_query
    await query.answer()
    title = query.data

    file_id = music_files.get(title.lower())
    if file_id:
        await query.message.reply_audio(audio=file_id)
    else:
        await query.message.reply_text("Файл табылган жок.")

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("BOT_TOKEN табылган жок!")

    threading.Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.AUDIO | filters.Document.AUDIO, upload_music)
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search_music)
    )

    app.run_polling()
