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

# Telegram токени
TOKEN = os.getenv("BOT_TOKEN")

# Render үчүн порт ачуу
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Music Bot is running")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

# Баштоо
async def start(update, context):
    await update.message.reply_text(
        "Салам! 🎵 Музыка ботко кош келиңиз!\n"
        "Ырдын атын жазыңыз."
    )

# Музыка издөө
async def message(update, context):
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
            await update.message.reply_text("Ыр табылган жок.")
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

        await update.message.reply_text(
            "Бул ырдын аудио үзүндүсү жок."
        )

    except Exception as e:
        print("Ката:", e)
        await update.message.reply_text("Издөөдө ката чыкты.")

# Ботту иштетүү
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("BOT_TOKEN табылган жок!")

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message)
    )

    print("🎵 Бот иштеп жатат!")
    app.run_polling()
