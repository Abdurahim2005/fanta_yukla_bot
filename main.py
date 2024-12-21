import logging
import os
import re
import threading
from telebot import TeleBot, apihelper
from yt_dlp import YoutubeDL
import requests

# Tokenni environment variable orqali oling
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN o'rnatilmagan. Iltimos, environment variable orqali tokenni taqdim qiling.")

bot = TeleBot(BOT_TOKEN)

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram API uchun sessiya sozlamalari
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    max_retries=5,  # Qayta urinishlar soni
    pool_connections=100,
    pool_maxsize=100,
)
session.mount("https://", adapter)
apihelper.SESSION = session

# YouTube URL tekshiruvi
def is_youtube_url(url: str) -> bool:
    return re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', url) is not None

# Haqiqiy video yuklash yoki mavjudini yuborish
def download_and_send_video(message, url):
    try:
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True,
        }

        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_path = ydl.prepare_filename(info)

            # Fayl mavjudligini tekshirish
            if os.path.exists(video_path):
                bot.reply_to(message, "✅ Video oldindan mavjud edi. Yuklanmoqda...")
            else:
                bot.reply_to(message, "🔄 Video yuklanmoqda. Iltimos, kuting...")
                ydl.download([url])

        # Foydalanuvchiga videoni yuborish
        with open(video_path, "rb") as video:
            bot.send_video(
                message.chat.id,
                video=video,
                caption=f"✅ Video yuklandi: {info.get('title', 'Video')}",
                timeout=300,
            )

        # Faylni o'chirish
        os.remove(video_path)
        logger.info(f"Fayl o'chirildi: {video_path}")

    except Exception as e:
        logger.error(f"Error during download: {e}")
        bot.reply_to(message, "❌ Yuklashda xatolik yuz berdi. Iltimos, boshqa havola yuboring.")

# /start komandasi
@bot.message_handler(commands=["start"])
def start_handler(message):
    bot.reply_to(message, "Assalomu alaykum! YouTube havolasini yuboring.")

# URLni qayta ishlash
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if is_youtube_url(url):
        threading.Thread(target=download_and_send_video, args=(message, url)).start()
    else:
        bot.reply_to(message, "❌ Xato: To'g'ri YouTube URL manzilini yuboring.")

# Botni ishga tushirish
if __name__ == "__main__":
    bot.polling(none_stop=True, timeout=300, long_polling_timeout=100)
