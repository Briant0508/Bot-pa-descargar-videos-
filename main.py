import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = '8374266654:AAHQzeo7C85kzHwdi1SjgeUlbO2xvU8MT8Y'

# 🧠 Diccionario para guardar enlaces por usuario
user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Envíame un enlace de video (YouTube, TikTok, etc.) y te mostraré las opciones de calidad disponibles.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    user_id = update.effective_user.id
    user_links[user_id] = link

    await update.message.reply_text("🔍 Analizando el video...")

    # Ejecutar yt-dlp para obtener formatos
    result = subprocess.run(
        ["yt-dlp", "-F", link],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    formats = []
    for line in result.stdout.splitlines():
        if line.strip().startswith(tuple(str(i) for i in range(10))):
            parts = line.split()
            if len(parts) >= 3:
                format_id = parts[0]
                resolution = parts[1]
                formats.append((format_id, resolution))

    if not formats:
        await update.message.reply_text("❌ No se encontraron formatos disponibles.")
        return

    # Crear botones de calidad
    buttons = [
        [InlineKeyboardButton(f"{res}", callback_data=f"{format_id}")]
        for format_id, res in formats[:5]  # Limitar a 5 opciones
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("📥 Elige la calidad:", reply_markup=reply_markup)

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    format_id = query.data
    user_id = query.from_user.id
    link = user_links.get(user_id)

    if not link:
        await query.edit_message_text("❌ No tengo registrado tu enlace. Envíalo de nuevo.")
        return

    filename = f"{user_id}_{format_id}.mp4"

    await query.edit_message_text("⏳ Descargando video...")

    subprocess.run([
        "yt-dlp", "-f", format_id, "-o", filename, link
    ])

    # Enviar el archivo
    try:
        await context.bot.send_video(chat_id=user_id, video=open(filename, "rb"))
        os.remove(filename)
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"⚠️ Error al enviar el video: {e}")

# 🚀 Configurar el bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(download_video))
app.run_polling()