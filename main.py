import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = 'TU_TOKEN_DE_TELEGRAM'

# 🧠 Diccionario para guardar enlaces y tipo de descarga por usuario
user_links = {}

# 🎬 Mensaje de bienvenida
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy tu bot descargador de videos y música.\n\n"
        "📥 Envíame un enlace de YouTube, TikTok, Instagram, etc.\n"
        "🎚️ Te mostraré las calidades disponibles para descargar el video.\n"
        "🎧 También puedes elegir descargar solo el audio en formato MP3.\n\n"
        "Escribe /help si necesitas ayuda."
    )

# 🆘 Comando de ayuda
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠️ **¿Cómo usar el bot?**\n\n"
        "1️⃣ Envía un enlace de video válido.\n"
        "2️⃣ El bot analizará el video y te mostrará las calidades disponibles.\n"
        "3️⃣ Elige la calidad o selecciona 'Solo audio (MP3)'.\n"
        "4️⃣ Recibirás el archivo directamente por Telegram.\n\n"
        "⚠️ Asegúrate de que el enlace sea público y accesible."
    )

# 📎 Manejo de enlaces
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()
    user_id = update.effective_user.id

    if not link.startswith("http"):
        await update.message.reply_text("❌ Ese no parece un enlace válido. Intenta con uno de YouTube, TikTok, etc.")
        return

    user_links[user_id] = link
    await update.message.reply_text("🔍 Analizando el video...")

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
        await update.message.reply_text("❌ No se encontraron formatos disponibles para ese enlace.")
        return

    buttons = [
        [InlineKeyboardButton(f"{res}", callback_data=f"video_{format_id}")]
        for format_id, res in formats[:5]
    ]
    buttons.append([InlineKeyboardButton("🎧 Solo audio (MP3)", callback_data="audio_mp3")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("📥 Elige qué quieres descargar:", reply_markup=reply_markup)

# 📦 Descarga del archivo
async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    user_id = query.from_user.id
    link = user_links.get(user_id)

    if not link:
        await query.edit_message_text("❌ No tengo registrado tu enlace. Por favor, envíalo de nuevo.")
        return

    if choice.startswith("video_"):
        format_id = choice.split("_")[1]
        filename = f"{user_id}_{format_id}.mp4"
        await query.edit_message_text("⏳ Descargando video...")

        subprocess.run([