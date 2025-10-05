import telebot
from telebot import types
import yt_dlp
import os

BOT_TOKEN = os.getenv("8374266654:AAHQzeo7C85kzHwdi1SjgeUlbO2xvU8MT8Y")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "👋 Hola! Envíame un enlace de video para descargarlo.")

@bot.message_handler(func=lambda m: m.text.startswith("http"))
def handle_url(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🎞️ 360p", callback_data=f"360|{message.text}"),
        types.InlineKeyboardButton("🎞️ 240p", callback_data=f"240|{message.text}"),
        types.InlineKeyboardButton("🎞️ 144p", callback_data=f"144|{message.text}")
    )
    markup.row(
        types.InlineKeyboardButton("🎧 MP3", callback_data=f"mp3|{message.text}")
    )
    bot.send_message(message.chat.id, "Selecciona la calidad o formato:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def process_download(call):
    quality, url = call.data.split("|")
    bot.answer_callback_query(call.id, f"Descargando en {quality}...")

    if quality == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': 'audio.%(ext)s',
            'quiet': True
        }
        filename = "audio.mp3"
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True
        }
        filename = None

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if quality == "mp3":
        with open(filename, "rb") as f:
            bot.send_audio(call.message.chat.id, f)
        os.remove(filename)
    else:
        video_file = next((f for f in os.listdir() if f.startswith("video.")), None)
        if video_file:
            with open(video_file, "rb") as f:
                bot.send_video(call.message.chat.id, f)
            os.remove(video_file)

bot.polling()