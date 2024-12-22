import logging
import os
import re
import threading
from telebot import TeleBot, apihelper, types
from yt_dlp import YoutubeDL
import requests

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
    return re.match(r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/).+', url) is not None

# Fayl nomini tozalash funksiyasi
def sanitize_filename(filename):
    return re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')

# /start buyrug'iga javob
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🙂Assalomu alaykum! Botimizga xush kelibsiz!\n🌀Youtube havolasini yuboring, Men video va audioni yuklab berishim mumkin!")

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

def download_and_send_video(message, format_id, url):
    try:
        # Eski yuklashlarni tozalash
        clear_download_folder()

        # Telegram faoliyat belgisi (boshlash)
        action = "upload_audio" if format_id == "mp3" else "upload_video"
        bot.send_chat_action(chat_id=message.chat.id, action=action)

        ydl_opts = {
            "format": "bestaudio/best" if format_id == "mp3" else format_id,
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True,
            "noprogress": True,
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}] if format_id == "mp3" else [],
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }


        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            safe_title = re.sub(r'[<>:"/\\|?*]', '', info.get('title', 'no_title'))
            ext = "mp3" if format_id == "mp3" else "mp4"
            file_path = f"downloads/{safe_title}.{ext}"

        if not os.path.exists(file_path):
            bot.reply_to(message, "\u274C Faylni yuklab olishda xatolik yuz berdi.Agar xatolik davom etsa Admin bilan bog'laning")
            return

        if format_id == "mp3":
            # MP3 faylni yuborish
            with open(file_path, "rb") as file:
                bot.send_audio(
                    chat_id=message.chat.id,
                    audio=file,
                    caption=f"{info.get('title', 'Audio')}\n\n✅ Shunchaki foydalaning!\n@FantaYukla_bot",
                )
        else:
            # Audio yuklab olish (video uchun)
            audio_opts = {
                "format": "bestaudio",
                "outtmpl": "downloads/%(title)s_audio.%(ext)s",
                "quiet": True,
                "noprogress": True,
            }
            bot.send_chat_action(chat_id=message.chat.id, action="upload_video")
            with YoutubeDL(audio_opts) as ydl:
                audio_info = ydl.extract_info(url, download=True)
                audio_title = re.sub(r'[<>:"/\\|?*]', '', audio_info.get('title', 'no_title'))
                audio_path = f"downloads/{audio_title}_audio.{audio_info['ext']}"

            if not os.path.exists(audio_path):
                bot.reply_to(message, "\u274C Audio faylni yuklashda xatolik yuz berdi.Agar xatolik davom etsa Admin bilan bog'laning")
                return

            # Video va audiolarni birlashtirish
            merged_path = f"downloads/{safe_title}_merged.mp4"
            merge_command = f"ffmpeg -i \"{file_path}\" -i \"{audio_path}\" -c:v copy -c:a aac \"{merged_path}\" -y"
            merge_result = os.system(merge_command)

            if merge_result != 0 or not os.path.exists(merged_path):
                bot.reply_to(message, "\u274C Video va audio birlashtirishda xatolik yuz berdi.")
                return

            # Foydalanuvchiga birlashtirilgan video yuborish
            bot.send_chat_action(chat_id=message.chat.id, action="upload_video")
            with open(merged_path, "rb") as file:
                bot.send_video(
                    chat_id=message.chat.id,
                    video=file,
                    caption=f"🎥 {info.get('title', 'Video')}\n\n✅ Shunchaki foydalaning!\n@FantaYukla_bot",
                    supports_streaming=True,
                    timeout=600,
                )
        # Tozalash: Fayl yuborilgandan so'ng
        clear_download_folder()

    except Exception as e:
        bot.reply_to(message, f"\u274C Yuklashda xatolik yuz berdi: Agar xatolik davom etsa \n👮‍♂️Admin bilan bog'laning")
        clear_download_folder()  # Xatolikdan keyin ham fayllarni tozalash

# Foydalanuvchi xabarlarini sessiyada saqlash uchun
user_sessions = {}
# url bilan ishlash
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
                    # Foydali atributlarni olish
                    resolution = f.get("format_note", "unknown").lower()
                    filesize = f.get("filesize", None) or 0  # Agar None bo'lsa, 0 ga tenglash
                    ext = f.get("ext", "unknown")

                    # Filtrlash shartlari
                    if (
                        ext == "mp4" and
                        filesize > 0 and  # Fayl hajmi mavjudligini tekshirish
                        filesize <= 50 * 1024 * 1024 and
                        resolution not in ["default", "unknown", None]
                    ):
                        # Agar format yangi yoki kichikroq hajmga ega bo'lsa, uni saqlang
                        if resolution not in unique_formats or filesize < unique_formats[resolution].get("filesize", float("inf")):
                            unique_formats[resolution] = f

                # MP3 formatni qo'shish
                mp3_format = None
                for f in formats:
                    if f.get("ext") == "webm" and f.get("acodec") != "none":
                        mp3_format = f
                        break

                # Format hajmlari va tavsiflarni yaratish
                for resolution, f in unique_formats.items():
                    size_mb = f.get("filesize", 0) / (1024 * 1024)  # Fayl hajmini MB ga o'tkazish
                    format_details.append(f"🚀 {resolution.upper()}: {size_mb:.2f}MB")
                if mp3_format:
                    mp3_size_mb = mp3_format.get("filesize", 0) / (1024 * 338)  # MP3 hajmi
                    format_details.append(f"🎵 MP3: {mp3_size_mb:.2f}MB")

                # Agar hech bir format mos kelmasa
                if not unique_formats and not mp3_format:
                    bot.reply_to(
                        message,
                        "⚠️ Hech bir format 50 MB dan kichik emas. Iltimos, boshqa video tanlang."
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
                        f"🎥 **{title}**\n"
                        f"⏱️ **Davomiyligi**: {duration_str}\n\n"
                        "📥 **Mavjud formatlar:**\n\n" + "\n".join(format_details)
                    ),
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )

        except Exception as e:
            logger.error(f"Xatolik video yuklashda: {e}")
            bot.reply_to(message, "❌ Yuklashda xatolik yuz berdi. Iltimos, boshqa havolani sinab ko'ring.Agar xatolik davom etsa Admin bilan bog'laning")
    else:
        bot.reply_to(message, "\u274C Xato: To'g'ri YouTube URL manzilini yuboring.")
        
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
