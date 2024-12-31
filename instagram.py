import os
from yt_dlp import YoutubeDL

# Instagram videolarini yuklab olish funksiyasi
def download_instagram_video(url: str) -> str:
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': 'instagram_video.mp4',  # Yuklab olingan fayl nomi
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return "instagram_video.mp4"
        except Exception as e:
            if "private" in str(e).lower():
                raise ValueError(
                    "❗️Bu video yopiq akkauntga tegishli bo'lishi mumkin.\n😕Hozirga bu videoni yuklab olish imkoni yo'q.\n👨‍💻Adminlar bu muammo ustida ishlashmoqda!"
                )
            else:
                raise e
