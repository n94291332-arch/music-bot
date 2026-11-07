import os, asyncio, tempfile, glob, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import yt_dlp
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler,
                          MessageHandler, filters, ContextTypes)

TOKEN = os.environ["TOKEN"]

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, *a):
        pass

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), H).serve_forever()

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши название песни, я найду 🎵")

def download(query, folder):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{folder}/%(title)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "default_search": "scsearch1",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if info and "entries" in info:
            info = info["entries"][0] if info["entries"] else None
        return info

async def search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Издеп жатам... ⏳")
    with tempfile.TemporaryDirectory() as folder:
        try:
            info = await asyncio.to_thread(download, update.message.text, folder)
            files = glob.glob(f"{folder}/*.mp3")
            if not info or not files:
                await msg.edit_text("Таба албадым 😕")
                return
            if os.path.getsize(files[0]) > 49 * 1024 * 1024:
                await msg.edit_text("Файл өтө чоң (50 МБ'дан ашты) 😕")
                return
            with open(files[0], "rb") as f:
                await update.message.reply_audio(f, title=info.get("title"))
            await msg.delete()
        except Exception as e:
            await msg.edit_text("Ката чыкты, кайра аракет кылыңыз.")
            print(e)

threading.Thread(target=run_web, daemon=True).start()

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
app.run_polling()
