# Python image tanlanadi
FROM python:3.11

# Ishchi katalogni yaratish
WORKDIR /app

# Kutubxonalarni o‘rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot fayllarini yuklash
COPY . .

# Botni ishga tushirish
CMD ["python", "main.py"]
