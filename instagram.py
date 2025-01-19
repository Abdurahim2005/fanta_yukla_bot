import os
import re
import requests
from yt_dlp import YoutubeDL
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# Videoni yuklab olish funksiyasi
def download_video_with_audio(url: str, downloads_folder: str = 'Downloads', output_filename: str = 'downloaded_video.mp4') -> str:
    # Yuklab olish yo'lini belgilash
    output_path = os.path.join(downloads_folder, output_filename)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': output_path,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        return output_path
    except Exception as e:
        if "private" in str(e).lower():
            raise ValueError("❗️Bu video yopiq akkauntga tegishli bo'lishi mumkin. Uni yuklab bo'lmaydi.")
        raise ValueError(f"Videoni yuklab olishda xatolik: {e}")

# Instagram rasmlarini yuklab olish funksiyasi
def download_instagram_images_with_selenium(url: str, downloads_folder: str = 'Downloads') -> list:
    downloaded_files = []
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//img')))
        images = driver.find_elements(By.XPATH, '//img[contains(@src, "cdninstagram")]')
        image_urls = list(set(img.get_attribute('src') for img in images))

        # Har bir rasmni yuklab olish
        for idx, image_url in enumerate(image_urls, start=1):
            output_filename = f'image_{idx}.jpg'
            output_path = os.path.join(downloads_folder, output_filename)
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                downloaded_files.append(output_path)
    except Exception as e:
        raise ValueError(f"Rasmlarni yuklab olishda xatolik: {e}")
    finally:
        driver.quit()
    return downloaded_files

# Media yuklash funksiyasi
def download_media(url: str, downloads_folder: str = 'Downloads') -> str:
    instagram_photo_regex = r"https://www\.instagram\.com/p/[\w\-]+/"
    if re.match(instagram_photo_regex, url):
        return download_instagram_images_with_selenium(url, downloads_folder)
    return download_video_with_audio(url, downloads_folder)
