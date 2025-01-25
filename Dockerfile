# Python image asosida tasvir yaratish
FROM python:3.13-slim

# FFmpeg o'rnatish
RUN apt-get update && apt-get install -y ffmpeg

# Ishchi katalogni sozlash
WORKDIR /app

# Python loyihangiz fayllarini konteynerga nusxalash
COPY . /app

# Python kutubxonalarini o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Botni ishga tushirish uchun buyruq
CMD ["python", "main.py"]
