import os
import requests
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text(
        "Салам! 🎵 Ырдын атын жаз."
    )

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
            "Аудио үзүндүсү табылган жок."
        )

    except Exception as e:
        print(e)
        await update.message.reply_text("Ката чыкты.")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, message)
)

print("Бот иштеп жатат!")
app.run_polling()
