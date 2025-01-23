import os
import re
import requests
from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup
# Videoni yuklab olish funksiyasi
def download_video_with_audio(url: str, downloads_folder: str = 'Downloads', output_filename: str = 'downloaded_video.mp4') -> str:
    # To'liq chiqish yo'lini hosil qilish
    output_path = os.path.join(downloads_folder, output_filename)
    
    # YoutubeDL uchun sozlamalar
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': output_path,  # Yuklab olingan fayl nomi va yo'li
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return output_path
        except Exception as e:
            if "private" in str(e).lower():
                raise ValueError(
                    "😕Hozirga bu videoni yuklab olish imkoni yo'q.\n👨‍💻Adminlar bu muammo ustida ishlashmoqda!\nBot serverdan uzilib qolishi kuzatilyapti\nAdmin botni bu xabarni ko'rishi bilan ishga tushiradi\nAgar server bilan bog'liq muammo bo'lmasa,demak hozirda bu mediyani yuklab olish imkonsiz!☝️Botga yana bir bor havolani yuborib ko'ring,bu xolat takrorlansa\n🤔Admin bu muammoni hal qilishga harakat qiladi✅"
                )
            else:
                raise e

# Instagram rasmlarini yuklab olish funksiyasi
def download_instagram_images(url: str, downloads_folder: str = 'Downloads') -> list:
    """
    Instagram postidagi barcha rasmlarni yuklab olish funksiyasi.
    :param url: Instagram postining URL manzili
    :param downloads_folder: Yuklab olish uchun papka (default: 'Downloads')
    :return: Yuklab olingan fayllar ro'yxati
    """
    # Yuklab olingan fayllar ro'yxati
    downloaded_files = []

    try:
        # Sahifani yuklash
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Sahifani parsing qilish
        soup = BeautifulSoup(response.text, 'html.parser')

        # Rasmlar URL'larini topish
        image_tags = soup.find_all('meta', {'property': 'og:image'})
        image_urls = [tag['content'] for tag in image_tags]

        # Agar rasmlar topilmasa xatolik qaytarish
        if not image_urls:
            raise ValueError("❗️Instagram havolasidan rasm URL'larini topib bo'lmadi.")

        # Har bir rasmni yuklab olish
        for idx, image_url in enumerate(image_urls, start=1):
            # Fayl nomini yaratish
            output_filename = f'image_{idx}.jpg'
            output_path = os.path.join(downloads_folder, output_filename)

            # Rasmni yuklab olish
            img_data = requests.get(image_url).content
            with open(output_path, 'wb') as handler:
                handler.write(img_data)

            # Yuklangan faylni ro'yxatga qo'shish
            downloaded_files.append(output_path)

        return downloaded_files

    except Exception as e:
        raise ValueError(f"Rasmlarni yuklab olishda xatolik: {e}")

# Media yuklash funksiyasi
def download_media(url: str, downloads_folder: str = 'Downloads') -> str:
    # Instagram rasmlarini yuklashni tekshirish uchun regex
    instagram_photo_regex = r"https://www\.instagram\.com/p/[\w\-]+/"
    
    if re.match(instagram_photo_regex, url):
        # Agar bu Instagram rasmiga tegishli havola bo'lsa
        return download_instagram_images(url, downloads_folder)
    else:
        # Qolgan barcha havolalar uchun video yuklash
        return download_video_with_audio(url, downloads_folder)
