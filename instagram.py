import os
from yt_dlp import YoutubeDL

# Downloads papkasini tozalash funksiyasi
def clear_downloads_folder(folder_path: str):
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)  # Faylni o'chirish
            except Exception as e:
                print(f"❗️ Faylni o'chirishda xato: {file_path}. Xato: {e}")

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

# Asosiy jarayon
def main():
    downloads_folder = 'Downloads'

    # Yuklashni boshlashdan oldin papkani tozalash
    print("📂 Downloads papkasini tozalash...")
    clear_downloads_folder(downloads_folder)

    # Yuklab olish
    video_url = input("Videoning URL manzilini kiriting: ")
    try:
        print("📥 Videoni yuklab olish boshlandi...")
        downloaded_file = download_video_with_audio(video_url, downloads_folder)
        print(f"✅ Video muvaffaqiyatli yuklandi: {downloaded_file}")
    except Exception as e:
        print(f"❌ Yuklab olishda xato yuz berdi: {e}")

    # Ish tugaganidan so'ng papkani tozalash
    print("📂 Ish tugadi. Downloads papkasini yana tozalash...")
    clear_downloads_folder(downloads_folder)
