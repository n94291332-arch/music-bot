import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")


def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Салам! MP3 музыка жөнөт — бот аны Telegram ичинде чыгарат."
    )


async def upload_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.audio:
        file_id = msg.audio.file_id
        title = msg.audio.title or msg.audio.file_name or "Музыка"
        artist = msg.audio.performer or "Белгисиз"

    elif msg.document and msg.document.mime_type == "audio/mpeg":
        file_id = msg.document.file_id
        title = msg.document.file_name or "Музыка"
        artist = "Белгисиз"

    else:
        await msg.reply_text("MP3 аудио файл жөнөт.")
        return

    await msg.reply_audio(
        audio=file_id,
        title=title,
        performer=artist,
        caption=f"🎵 {title}\n👤 {artist}"
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

    app.run_polling()
