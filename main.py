import os
import time
import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL
import re

# Telegram bot sozlamalari
API_ID = "29517932"
API_HASH = "572b177f48692c0cbd88664120fb87f4"
BOT_TOKEN = "7901083872:AAHIZSZZD5EWtRdXX8tQwSNou7hh7LqoskQ"
ADMIN_ID = 1663567950

app = Client("video_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Yuklab olish uchun funksiyalar
async def download_video(url, message):
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        'format': 'best',
        'cookiefile': 'cookies.txt'  # <-- COOKIES YO‘LNI KO‘SHING
    }
    
    msg = await message.reply("📥 Yuklab olinmoqda...")
    status_msg_id = msg.id
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('percentage', 0)
            asyncio.create_task(message.edit(f"⏳ Yuklanmoqda: {percent:.2f}%"))
    
    ydl_opts['progress_hooks'] = [progress_hook]
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
        
        caption = "✅ Shunchaki foydalaning\n\n@FantaYukla_bot"
        user_info = f"👤 User: {message.from_user.mention} (ID: {message.from_user.id})"
        
        # Foydalanuvchiga video yuborish
        await message.reply_video(video=video_path, caption=caption)
        
        # Admin uchun video yuborish
        admin_msg = await app.send_message(ADMIN_ID, f"📩 Yangi video yuklandi!\n{user_info}\n🔗 {url}")
        await app.send_video(ADMIN_ID, video=video_path, caption=user_info, reply_to_message_id=admin_msg.id)
        
        os.remove(video_path)
    except Exception as e:
        error_message = f"❌ Xatolik yuz berdi: {str(e)}"
        await message.reply(error_message)
        await app.send_message(ADMIN_ID, f"⚠️ Xatolik yuz berdi!\n{user_info}\n🔗 {url}\n❌ {str(e)}")
    
    await message.delete()  # Eski xabarlarni tozalash
    await app.delete_messages(message.chat.id, status_msg_id)

@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message):
    await message.reply("👋 Salom! Menga video havolasini yuboring, men uni yuklab beraman.")

@app.on_message(filters.private & filters.text & ~filters.user(ADMIN_ID))
async def handle_message(client, message):
    url = message.text.strip()
    user_info = f"👤 User: {message.from_user.mention} (ID: {message.from_user.id})"
    
    # Adminga foydalanuvchi xabarini yuborish
    admin_msg = await app.send_message(ADMIN_ID, f"📩 {user_info} botga quyidagi xabarni yubordi:\n{url}")
    
    if url.startswith("http"):
        await message.delete()
        await download_video(url, message)
    else:
        error_message = "❌ Iltimos, to'g'ri havola yuboring!"
        await message.reply(error_message)
        await app.send_message(ADMIN_ID, f"⚠️ Xatolik! {user_info} noto‘g‘ri havola yubordi: {url}")

@app.on_message(filters.private & filters.reply & filters.user(ADMIN_ID))
async def reply_to_user(client, message):
    if message.reply_to_message:
        user_id_match = re.search(r'ID: (\d+)', message.reply_to_message.text)
        if user_id_match:
            user_id = int(user_id_match.group(1))
            await app.send_message(user_id, f"📩 Admin javobi:\n{message.text}")
            await message.reply("✅ Xabar foydalanuvchiga yuborildi.")
        else:
            await message.reply("⚠️ Ushbu xabarda foydalanuvchi ID topilmadi.")
    else:
        await message.reply("⚠️ Ushbu xabar orqali foydalanuvchini aniqlab bo‘lmadi.")

app.run()
