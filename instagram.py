import os
import re
import requests
from yt_dlp import YoutubeDL
from selenium import webdriver
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import time

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
                    "❗️Bu video yopiq akkauntga tegishli bo'lishi mumkin.\n😕Hozirga bu videoni yuklab olish imkoni yo'q.\n👨‍💻Adminlar bu muammo ustida ishlashmoqda!"
                )
            else:
                raise e

# Instagram rasmlarini yuklab olish funksiyasi
def download_instagram_images_with_selenium(url: str, downloads_folder: str = '/tmp/') -> list:
    """
    Instagram postidagi barcha rasmlarni Selenium yordamida yuklab olish funksiyasi.
    :param url: Instagram postining URL manzili
    :param downloads_folder: Yuklab olish uchun papka (default: '/tmp/')
    :return: Yuklab olingan fayllar ro'yxati
    """
    # Yuklab olingan fayllar ro'yxati
    downloaded_files = []

    try:
        # ChromeDriver avtomatik o'rnatish
        chromedriver_autoinstaller.install()

        # Selenium uchun driver sozlash
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # GUI ko'rsatilmasin
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)

        # Instagram sahifasiga o'tish
        driver.get(url)
        time.sleep(5)  # Sahifaning to'liq yuklanishini kutish

        # Rasmlar URL'larini olish
        images = driver.find_elements(By.XPATH, '//img[contains(@src, "cdninstagram")]')
        image_urls = list(set(img.get_attribute('src') for img in images))  # Dublikat URL'larni yo'q qilish

        # Yuklab olish uchun papka mavjudligini tekshirish yoki yaratish
        os.makedirs(downloads_folder, exist_ok=True)

        # Har bir rasmni yuklab olish
        for idx, image_url in enumerate(image_urls, start=1):
            # Fayl nomini yaratish
            output_filename = f'image_{idx}.jpg'
            output_path = os.path.join(downloads_folder, output_filename)

            # Rasmni yuklab olish
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                # Yuklangan faylni ro'yxatga qo'shish
                downloaded_files.append(output_path)

        # Selenium sessiyasini yopish
        driver.quit()

        return downloaded_files

    except Exception as e:
        raise ValueError(f"Rasmlarni yuklab olishda xatolik: {e}")
    
# Media yuklash funksiyasi
def download_media(url: str, downloads_folder: str = 'Downloads') -> str:
    # Instagram rasmlarini yuklashni tekshirish uchun regex
    instagram_photo_regex = r"https://www\.instagram\.com/p/[\w\-]+/"
    
    if re.match(instagram_photo_regex, url):
        # Agar bu Instagram rasmiga tegishli havola bo'lsa
        return download_instagram_images_with_selenium(url, downloads_folder)
    else:
        # Qolgan barcha havolalar uchun video yuklash
        return download_video_with_audio(url, downloads_folder)
