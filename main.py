import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = '8374266654:AAHQzeo7C85kzHwdi1SjgeUlbO2xvU8MT8Y'  # ← Reemplaza esto con tu token real

user_links = {}

# 🔍 Obtener título del video
def get_video_title(link):
    result = subprocess.run(
        ["yt-dlp", "--get-title", link],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip() or "audio"

# 👋 Mensaje de bienvenida
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
        "🛠️ ¿Cómo usar el bot?\n\n"
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
            if len(parts) >= 5:
                format_id = parts[0]
                ext = parts[1]
                resolution = parts[2]
                size = parts[-1] if "MiB" in parts[-1] or "GiB" in parts[-1] else "?"
                label = f"{resolution} - {ext} - {size}"
                formats.append((format_id, label))

    if not formats:
        await update.message.reply_text("❌ No se encontraron formatos disponibles para ese enlace.")
        return

    buttons = [
        [InlineKeyboardButton(label, callback_data=f"video_{format_id}")]
        for format_id, label in formats[:5]
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

    try:
        subprocess.run([
            "yt-dlp", "-f", format_id, link, "-o", filename
        ])
        await context.bot.send_video(chat_id=user_id, video=open(filename, "rb"))
        os.remove(filename)
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"⚠️ Error al enviar el video: {e}")

elif choice == "audio_mp3":
    title = get_video_title(link)
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
    filename = f"{safe_title}.mp3"
    await query.edit_message_text("🎧 Extrayendo audio en MP3...")

    try:
        subprocess.run([
            "yt-dlp", "-x", "--audio-format", "mp3", "-o", filename, link
        ])
        await context.bot.send_audio(chat_id=user_id, audio=open(filename, "rb"), title=title)
        os.remove(filename)
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"⚠️ Error al enviar el audio: {e}")