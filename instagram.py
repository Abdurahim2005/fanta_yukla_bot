import os
import re
import requests
from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup

# Videoni yuklab olish funksiyasi
def download_video_with_audio(url: str, downloads_folder: str = 'Downloads', output_filename: str = 'downloaded_video.mp4') -> str:
    os.makedirs(downloads_folder, exist_ok=True)  # Papkani yaratish agar mavjud bo'lmasa
    output_path = os.path.join(downloads_folder, f"{output_filename}.mp4")  

    # YoutubeDL uchun yangi versiyaga mos sozlamalar
    ydl_opts = {
        'format': 'bv*+ba/b',  # Eng yaxshi video va audio formatini tanlash
        'outtmpl': output_path,
        'noprogress': True,  # Konsolda progress bar chiqmasligi uchun
        'logger': None,  # Xatoliklarni konsolda ko‘rsatmaslik uchun
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            return output_path
        except Exception as e:
            if "private" in str(e).lower():
                raise ValueError("😕 Hozir bu videoni yuklab olish mumkin emas.")
            else:
                raise e

# Instagram rasmlarini yuklab olish funksiyasi
def download_instagram_images(url: str, downloads_folder: str = 'Downloads') -> list:
    downloaded_files = []
    os.makedirs(downloads_folder, exist_ok=True)  

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        image_tags = soup.find_all('meta', {'property': 'og:image'})
        image_urls = [tag['content'] for tag in image_tags]

        if not image_urls:
            raise ValueError("❗️ Instagram rasmlarini topib bo‘lmadi.")

        for idx, image_url in enumerate(image_urls, start=1):
            output_filename = f'image_{idx}.jpg'
            output_path = os.path.join(downloads_folder, output_filename)

            img_data = requests.get(image_url).content
            with open(output_path, 'wb') as handler:
                handler.write(img_data)

            downloaded_files.append(output_path)

        return downloaded_files

    except Exception as e:
        raise ValueError(f"Rasmlarni yuklab olishda xatolik: {e}")

# Media yuklash funksiyasi
def download_media(url: str, downloads_folder: str = 'Downloads') -> str:
    instagram_photo_regex = r"https://www\.instagram\.com/p/[\w\-]+/"
    
    if re.match(instagram_photo_regex, url):
        return download_instagram_images(url, downloads_folder)
    else:
        return download_video_with_audio(url, downloads_folder)
