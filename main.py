import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola 👋 Envíame un enlace de video para descargar.")

# Recibir enlace y mostrar opciones
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data["url"] = url

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "Sin título")
            duration = info.get("duration", 0)
            desc = info.get("description", "Sin descripción")[:200]

        keyboard = [
            [InlineKeyboardButton("🎧 MP3", callback_data="mp3")],
            [InlineKeyboardButton("📹 360p", callback_data="360p"),
             InlineKeyboardButton("📹 720p", callback_data="720p"),
             InlineKeyboardButton("📹 1080p", callback_data="1080p")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"*Título:* {title}\n*Duración:* {duration}s\n*Descripción:* {desc}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Error al analizar el enlace: {e}")

# Descargar según formato elegido
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get("url")
    choice = query.data

    await query.edit_message_text(f"Descargando en formato {choice}...")

    if choice == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
        filename = "audio.mp3"
    else:
        format_map = {
            "360p": "best[height<=360]",
            "720p": "best[height<=720]",
            "1080p": "best[height<=1080]"
        }
        ydl_opts = {
            'format': format_map[choice],
            'outtmpl': 'video.%(ext)s'
        }
        filename = "video.mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await query.message.reply_document(document=open(filename, "rb"))
        os.remove(filename)
    except Exception as e:
        await query.message.reply_text(f"Error al descargar: {e}")

# Configurar bot
app_bot = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app_bot.add_handler(CallbackQueryHandler(button))
app_bot.run_polling()