import logging
import os
import re
import threading
from telebot import TeleBot, apihelper, types
from yt_dlp import YoutubeDL
import requests
from instagram import download_instagram_video  # Instagram videolarini yuklab olish funksiyasini import qilamiz

# Bot tokenini kiriting
BOT_TOKEN = "7901083872:AAEceZ0Bu-8yKg0RkRObiJMR51kPWKzbqVM"

# Bot obyektini yaratish
bot = TeleBot(BOT_TOKEN)

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram API uchun sessiya sozlamalari
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    max_retries=10,  # Qayta urinishlar sonini oshiring
    pool_connections=100,
    pool_maxsize=100,
)
session.mount("https://", adapter)
session.mount("http://", adapter)
apihelper.SESSION = session

# YouTube URL tekshiruvi
def is_youtube_url(url: str) -> bool:
    return re.match(r'(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/).+', url) is not None

# Instagram URL ni aniqlash uchun regex
def is_instagram_url(url):
    return re.match(r'(https?://)?(www\.)?instagram\.com/.+', url) is not None

# Fayl nomini tozalash funksiyasi
def sanitize_filename(filename):
    return re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')

# /start buyrug'iga javob
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🙂Assalomu alaykum! Botimizga xush kelibsiz!\n🌀Youtube havolasini yuboring, Men video va audioni yuklab berishim mumkin!\n🩸Instagram havolasini ham yuborishingiz mumkin.")

# Formatlar haqida ma'lumotni foydalanuvchiga yuborish
def get_formats_description(formats):
    descriptions = []
    for f in formats:
        if f.get('ext') == 'mp4' and f.get('filesize', 0) <= 50 * 1024 * 1024:
            resolution = f.get('format_note', 'Unknown')
            size_mb = round(f.get('filesize', 0) / (1024 * 1024), 2)
            if resolution.lower() not in ["default", "unknown", "none"]:
                descriptions.append(f"🚀 {resolution}")
    # Faqat MP3 tugmasi mavjud bo‘lganda qo‘shish
    if "mp3" not in [f.get('ext') for f in formats]:
        descriptions.append("🎵 MP3")  # MP3 formatini qo‘shish
    return "\n".join(descriptions)

def create_format_buttons(formats, include_mp3=False):
    unique_formats = set()
    buttons = []

    for f in formats:
        if f.get('ext') == 'mp4' and f.get('filesize', 0) <= 50 * 1024 * 1024:
            resolution = f.get('format_note', 'Unknown')
            if resolution.lower() not in ["default", "unknown", "none"]:
                if resolution not in unique_formats:
                    unique_formats.add(resolution)
                    buttons.append(
                        types.InlineKeyboardButton(
                            text=f"🚀 {resolution}",
                            callback_data=f"format:{f['format_id']}"
                        )
                    )
    # MP3 formatini qo‘shish
    if include_mp3:
        buttons.append(
            types.InlineKeyboardButton(
                text="🎵 MP3", callback_data="format:mp3"
            )
        )
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    for i in range(0, len(buttons), 3):
        keyboard.add(*buttons[i:i+3])
    return keyboard

def clear_download_folder():
    """Vaqtinchalik fayllarni tozalash."""
    folder = "downloads"
    if os.path.exists(folder):
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Faylni o'chirishda xatolik: {file_path}, {e}")

import unicodedata
def clean_surrogates(text):
    """
    Unicode surrogat belgilarni olib tashlaydi.
    """
    try:
        # Unicode normalizatsiyasi
        text = unicodedata.normalize("NFKD", text)
        # Surrogat belgilarni olib tashlash
        text = re.sub(r"[\ud800-\udfff]", "", text)
        return text
    except Exception as e:
        raise ValueError(f"Surrogatlarni tozalashda xatolik: {e}")

def download_and_send_video(message, format_id, url):
    try:
        # URL va foydalanuvchi ma'lumotlarini tozalash
        url = clean_surrogates(url)

        # Eski yuklashlarni tozalash
        clear_download_folder()
        bot.reply_to(message, "⏳ Fayl yuklanmoqda, kuting...")

        # Telegram faoliyat belgisi
        action = "upload_audio" if format_id == "mp3" else "upload_video"
        bot.send_chat_action(chat_id=message.chat.id, action=action)

        # Fayl nomlari
        video_filename = "downloads/video_file.mp4"
        audio_filename = "downloads/audio_file.mp3"
        merged_filename = "downloads/merged_video.mp4"

        # YouTubeDL parametrlari
        ydl_opts = {
            "format": "bestaudio/best" if format_id == "mp3" else format_id,
            "outtmpl": "downloads/%(title)s.%(ext)s" if format_id == "mp3" else video_filename,
            "quiet": True,
            "noprogress": True,
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}] if format_id == "mp3" else [],
            "http_headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        # Faylni yuklab olish
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Fayl nomini aniqlash
        if format_id == "mp3":
            downloaded_filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            if not os.path.exists(downloaded_filename):
                bot.reply_to(message, "❌ Faylni yuklab olishda xatolik yuz berdi.")
                return

            os.rename(downloaded_filename, audio_filename)
            file_path = audio_filename
        else:
            file_path = video_filename

        # Faylni yuborish
        if format_id == "mp3":
            with open(file_path, "rb") as file:
                bot.send_audio(
                    chat_id=message.chat.id,
                    audio=file,
                    caption=f"🎵 {info.get('title', 'Audio')}\n\n✅ Shunchaki foydalaning!\n@FantaYukla_bot"
                )
        else:
            # Video uchun audio yuklash
            audio_opts = {
                "format": "bestaudio",
                "outtmpl": audio_filename,
                "quiet": True,
                "noprogress": True,
            }

            with YoutubeDL(audio_opts) as ydl:
                ydl.extract_info(url, download=True)

            if not os.path.exists(audio_filename):
                bot.reply_to(message, "❌ Audio faylni yuklashda xatolik yuz berdi.")
                return

            # Video va audio birlashtirish
            merge_command = f"ffmpeg -i \"{video_filename}\" -i \"{audio_filename}\" -c:v copy -c:a aac \"{merged_filename}\" -y"
            merge_result = os.system(merge_command)

            if merge_result != 0 or not os.path.exists(merged_filename):
                bot.reply_to(message, "❌ Video va audio birlashtirishda xatolik yuz berdi.")
                return

            # Birlashtirilgan video yuborish
            with open(merged_filename, "rb") as file:
                bot.send_video(
                    chat_id=message.chat.id,
                    video=file,
                    caption=f"🎥 {info.get('title', 'Video')}\n\n✅ Shunchaki foydalaning!\n@FantaYukla_bot",
                    supports_streaming=True,
                    timeout=600
                )

        # Tozalash
        clear_download_folder()

    except Exception as e:
        bot.reply_to(message, f"❌ Yuklashda xatolik yuz berdi: {e}")
        clear_download_folder()

def escape_markdown(text, version=2):
    """
    Telegram Markdown uchun maxsus belgilarni qochirish.
    """
    if version == 1:
        escape_chars = r'_*\[\]()~`>#+-=|{}.!'
    elif version == 2:
        escape_chars = r'_*\[\]()~`>#+-=|{}.!'
    else:
        raise ValueError("Unsupported Markdown version. Use 1 or 2.")
    
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# Foydalanuvchi xabarlarini sessiyada saqlash uchun
user_sessions = {}
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()

    if is_youtube_url(url):
        bot.reply_to(message, "⏳ Ma'lumotlar yuklanmoqda...")
        try:
            ydl_opts = {"quiet": True, "force_generic_extractor": False}

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get("formats", [])
                thumbnail = info.get("thumbnail", "")
                title = info.get("title", "No Title")
                duration = info.get("duration", 0)

                # Video davomiyligini formatlash
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                seconds = duration % 60
                duration_str = (
                    f"{hours:02}:{minutes:02}:{seconds:02}"
                    if hours > 0
                    else f"{minutes:02}:{seconds:02}"
                )

                # Formatlarni ajratish va tekshirish
                unique_formats = {}
                format_details = []

                for f in formats:
                    resolution = f.get("format_note", "unknown").lower()
                    filesize = f.get("filesize", 0) or 0
                    ext = f.get("ext", "unknown")

                    if (
                        ext == "mp4"
                        and filesize > 0
                        and filesize <= 50 * 1024 * 1024
                        and resolution not in ["default", "unknown", None]
                    ):
                        if resolution not in unique_formats or filesize < unique_formats[resolution].get("filesize", float("inf")):
                            unique_formats[resolution] = f

                # MP3 formatni qo'shish
                mp3_format = None
                for f in formats:
                    if f.get("ext") == "webm" and f.get("acodec") != "none":
                        mp3_format = f
                        break

                # Format tafsilotlarini yaratish
                for resolution, f in unique_formats.items():
                    size_mb = f.get("filesize", 0) / (1024 * 1024)
                    format_details.append(escape_markdown(f"🚀 {resolution.upper()}: {size_mb:.2f}MB", version=2))

                if mp3_format:
                    mp3_size_mb = mp3_format.get("filesize", 0) / (1024 * 1024)
                    format_details.append(escape_markdown(f"🎵 MP3: {mp3_size_mb:.2f}MB", version=2))

                # Agar hech bir format mos kelmasa
                if not unique_formats and not mp3_format:
                    bot.reply_to(
                        message,
                        "⚠️ Hech bir format 50 MB dan kichik emas. Iltimos, boshqa video tanlang.\n🛡Telegram cheklovlari tufayli bu videoni yuklab olish imkonsiz👨‍💻Adminlar bu muammo ustida ish olib borishmoqda."
                    )
                    return

                # Tugmalarni yaratish
                keyboard = create_format_buttons(list(unique_formats.values()), include_mp3=bool(mp3_format))

                # Sessiyani saqlash
                user_sessions[message.chat.id] = url

                # Foydalanuvchiga xabar yuborish
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    caption=(
                        f"🎥 *{escape_markdown(title, version=2)}*\n"
                        f"⏱️ *Davomiyligi*: {duration_str}\n\n"
                        "📥 *Mavjud formatlar:*\n\n" + "\n".join(format_details)
                    ),
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                )

        except Exception as e:
            logger.error(f"Xatolik video yuklashda: {e}", exc_info=True)
            bot.reply_to(message, "❌ Yuklashda xatolik yuz berdi. Iltimos, boshqa havolani sinab ko'ring.")

    elif is_instagram_url(url):
        # Foydalanuvchi yuborgan havolani qabul qilib chatdan o'chirish
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            print(f"Xatolik foydalanuvchi xabarini o'chirishda: {e}\nXatolik davom etsa Admin bilan bog'laning @Abdurahim0525")

        # Instagram havolasi haqida foydalanuvchiga xabar berish
        status_message = bot.send_message(
            message.chat.id,
            "⏳Video yuklanmoqda, kuting..."
        )

        try:
            # Instagram video yuklab olish
            video_path = download_instagram_video(url)

            # Bot holatini o'zgartirish: video yubormoqda
            bot.send_chat_action(message.chat.id, action="upload_video")

            # Yuklangan videoni foydalanuvchiga yuborish
            with open(video_path, 'rb') as video:
                bot.send_video(
                    chat_id=message.chat.id,
                    video=video,
                    caption=" 😊Shunchaki foydalaning\n@FantaYukla_bot"
                )

            # Yuklangan videoni o'chirish
            os.remove(video_path)

        except ValueError as ve:
            bot.send_message(message.chat.id, f"Xatolik: {ve}")
        except Exception as e:
            bot.send_message(message.chat.id, f"❗️Bu video yopiq akkauntga tegishli bo'lishi mumkin.\n_______________________\n😕Hozirga bu videoni yuklab olish imkoni yo'q.\n👨‍💻Adminlar bu muammo ustida ishlashmoqda!")
        finally:
            # "Yuklab olish boshlandi..." xabarini o'chirish
            try:
                bot.delete_message(message.chat.id, status_message.message_id)
            except Exception as e:
                print(f"Xatolik status xabarni o'chirishda: {e}\nXatolik davom etsa @Abdurhim0525 bilan bog'laning")

    else:
        bot.reply_to(message, "\u274C Xato: To'g'ri YouTube yoki Instagram URL manzilini yuboring.")
        
@bot.callback_query_handler(func=lambda call: call.data.startswith("format:"))
def handle_format_callback(call):
    try:
        format_id = call.data.split(":")[1]

        # Reply URL ni sessiyadan olish
        url = user_sessions.get(call.message.chat.id)

        if not url:
            logger.warning("URL sessiyadan topilmadi.")
            bot.answer_callback_query(call.id, "\u274C URL topilmadi.")
            return

        # Yuklashni ishga tushirish
        threading.Thread(target=download_and_send_video, args=(call.message, format_id, url)).start()
        bot.answer_callback_query(call.id, "✅ Yuklash boshlandi...")
    except Exception as e:
        logger.error(f"Callback xatosi: {e}")
        bot.answer_callback_query(call.id, "\u274C Yuklashda xatolik yuz berdi.")
        
# Botni ishga tushirish
if __name__ == "__main__":
    bot.polling(none_stop=True, timeout=300, long_polling_timeout=100)
