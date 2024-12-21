# Python 3.9 asosidagi tasvir
FROM python:3.9

# FFmpeg o'rnatish
RUN apt-get update && apt-get install -y ffmpeg

# Ishchi papkani belgilash
WORKDIR /app

# Kodlarni yuklash
COPY . .

# Kutubxonalarni o'rnatish
RUN pip install -r requirements.txt

# Botni ishga tushirish
CMD ["python", "main.py"]
