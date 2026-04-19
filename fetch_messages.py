from telethon import TelegramClient
import asyncio
from datetime import datetime, timedelta
import os
import aiohttp
import aiofiles

API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']

CHANNELS = [
    '@channel_one',
    '@channel_two',
]

# پوشه ذخیره فایل‌ها
DOWNLOAD_FOLDER = 'downloads'

async def download_media(message, channel_name):
    """دانلود فایل پیام و ذخیره با اسم مناسب"""
    if not message.media:
        return None
    
    try:
        # ساخت اسم فایل: channel_name_date_id.ext
        date_str = message.date.strftime('%Y%m%d_%H%M%S')
        ext = message.file.ext or '.bin'
        filename = f"{channel_name}_{date_str}_{message.id}{ext}"
        
        # پاک کردن کاراکترهای نامعتبر از اسم فایل
        filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # دانلود فایل
        await message.download_media(file=filepath)
        return filepath
    except Exception as e:
        print(f"⚠️ خطا در دانلود فایل: {e}")
        return None

async def main():
    # ساخت پوشه دانلود اگه نیست
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start()
    
    since_time = datetime.now() - timedelta(days=1)
    
    all_data = []
    media_count = 0
    
    for channel in CHANNELS:
        print(f"📡 در حال بررسی {channel}...")
        
        async for msg in client.get_messages(channel, limit=200):
            if msg.date < since_time:
                continue
            
            # اطلاعات پیام
            msg_data = {
                'channel': channel,
                'date': msg.date.strftime('%Y-%m-%d %H:%M:%S'),
                'text': msg.text.strip() if msg.text and msg.text.strip() else '',
                'files': []
            }
            
            # اگه فایل داره، دانلودش کن
            if msg.media:
                filepath = await download_media(msg, channel[1:])  # حذف @ از اسم کانال
                if filepath:
                    msg_data['files'].append(filepath)
                    media_count += 1
                    print(f"   📁 دانلود شد: {filepath}")
            
            # فقط اگه متن یا فایل داشته باشه ذخیره کن
            if msg_data['text'] or msg_data['files']:
                all_data.append(msg_data)
    
    # ذخیره اطلاعات توی فایل JSON (بهتر از txt برای مدیریت)
    import json
    report = {
        'last_update': datetime.now().isoformat(),
        'total_messages': len(all_data),
        'total_files': media_count,
        'messages': all_data
    }
    
    with open('messages.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # همچنین یه فایل متنی ساده برای خوندن راحت
    with open('messages.txt', 'w', encoding='utf-8') as f:
        f.write(f"آخرین بروزرسانی: {datetime.now()}\n")
        f.write(f"کل پیام‌ها: {len(all_data)} | کل فایل‌ها: {media_count}\n")
        f.write("="*60 + "\n\n")
        
        for msg in all_data:
            f.write(f"📢 کانال: {msg['channel']}\n")
            f.write(f"🕐 زمان: {msg['date']}\n")
            if msg['text']:
                f.write(f"💬 متن: {msg['text']}\n")
            if msg['files']:
                f.write(f"📎 فایل‌ها:\n")
                for file in msg['files']:
                    f.write(f"   - {file}\n")
            f.write("-"*40 + "\n\n")
    
    print(f"\n✅ کار انجام شد!")
    print(f"   📝 {len(all_data)} پیام ذخیره شد")
    print(f"   📁 {media_count} فایل دانلود شد")
    print(f"   📂 فایل‌ها توی پوشه 'downloads/' هستن")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
