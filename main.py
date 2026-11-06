import os
import threading
import requests

from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")


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
        "🎵 Салам! Музыка ботко кош келиңиз!\n\n"
        "🔎 Ырдын атын жазыңыз.\n"
        "📁 Же MP3 файл жөнөтүңүз."
    )


# Ыр издөө
async def search_music(update, context):
    song = update.message.text

    await update.message.reply_text("🔎 Ыр изделүүдө...")

    try:
        response = requests.get(
            "https://itunes.apple.com/search",
            params={
                "term": song,
                "entity": "song",
                "limit": 5
            },
            timeout=20
        )

        data = response.json()

        if data["resultCount"] == 0:
            await update.message.reply_text("❌ Ыр табылган жок.")
            return

        for item in data["results"]:
            audio = item.get("previewUrl")

            if audio:
                await update.message.reply_audio(
                    audio=audio,
                    title=item.get("trackName", "Музыка"),
                    performer=item.get("artistName", "")
                )
                return

        await update.message.reply_text("Аудио үзүндүсү жок.")

    except Exception as e:
        print("Ката:", e)
        await update.message.reply_text("Издөөдө ката чыкты.")


# MP3 кабыл алуу
async def upload_music(update, context):
    msg = update.message

    if msg.audio:
        file_id = msg.audio.file_id
        title = msg.audio.title or msg.audio.file_name or "Музыка"
        performer = msg.audio.performer or ""

    elif msg.document and msg.document.mime_type:
        if not msg.document.mime_type.startswith("audio/"):
            await msg.reply_text("MP3 же аудио файл жөнөтүңүз.")
            return

        file_id = msg.document.file_id
        title = msg.document.file_name or "Музыка"
        performer = ""

    else:
        return

    await msg.reply_text("✅ Музыка кабыл алынды!")

    await msg.reply_audio(
        audio=file_id,
        title=title,
        performer=performer
    )


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

    print("🎵 Бот иштеп жатат!")
    app.run_polling()
