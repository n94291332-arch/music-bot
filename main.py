
import os
import io
import logging
import aiohttp

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
JAMENDO_ID = os.getenv("JAMENDO_CLIENT_ID")

ai = AsyncOpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Салам! Мен Musicnuobotмун!\n\n"
        "🤖 AI менен сүйлөшүү үчүн текст жаз.\n"
        "🎵 Музыка издөө: /music ырдын аты"
    )


async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Мисалы: /music piano"
        )
        return

    if not JAMENDO_ID:
        await update.message.reply_text(
            "Музыка API ачкычы орнотулган эмес."
        )
        return

    query = " ".join(context.args)

    await update.message.reply_text("🎵 Музыка изделүүдө...")

    url = "https://api.jamendo.com/v3.0/tracks/"

    params = {
        "client_id": JAMENDO_ID,
        "format": "json",
        "namesearch": query,
        "limit": 5,
        "audiodlformat": "mp32",
        "include": "licenses"
    }

    try:
        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.get(
                url, params=params
            ) as response:
                data = await response.json()

            tracks = data.get("results", [])

            track = next(
                (
                    t for t in tracks
                    if t.get("audiodownload_allowed")
                    and t.get("audiodownload")
                ),
                None
            )

            if not track:
                await update.message.reply_text(
                    "Бул аталышта жүктөөгө уруксат берилген ыр табылган жок."
                )
                return

            async with session.get(
                track["audiodownload"]
            ) as response:

                if response.status != 200:
                    await update.message.reply_text(
                        "Музыканы алуу мүмкүн болгон жок."
                    )
                    return

                audio = await response.read()

            if len(audio) > 19 * 1024 * 1024:
                await update.message.reply_text(
                    "Файл өтө чоң экен."
                )
                return

            filename = io.BytesIO(audio)
            filename.name = "music.mp3"

            await update.message.reply_audio(
                audio=filename,
                title=track.get("name", "Music"),
                performer=track.get("artist_name", "Unknown")
            )

            await update.message.reply_text(
                "Музыканын лицензиясы: "
                + track.get("license_ccurl", "Маалымат жок")
            )

    except Exception:
        logging.exception("Music error")
        await update.message.reply_text(
            "Ката чыкты. Кийин кайра аракет кыл."
        )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ai:
        await update.message.reply_text(
            "AI API ачкычы орнотулган эмес."
        )
        return

    question = update.message.text

    await update.message.reply_text("🤖 Ойлонуп жатам...")

    try:
        result = await ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Сен кыргызча жооп берген пайдалуу AI жардамчысысың."
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        answer = result.choices[0].message.content

        await update.message.reply_text(
            answer[:4000]
        )

    except Exception:
        logging.exception("AI error")
        await update.message.reply_text(
            "AI менен байланышууда ката чыкты."
        )


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN орнотулган эмес")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", music))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat
        )
    )

    print("Musicnuobot иштеп жатат!")

    app.run_polling()


if __name__ == "__main__":
    main()
            
