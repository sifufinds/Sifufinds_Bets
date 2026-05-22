"""
Run this ONCE to log in to Telegram and get your session string.
After this you never need to touch Telegram setup again.

Run: python3 get_telegram_session.py
Then enter the SMS code Telegram sends to +447984336672
Copy the session string it prints and paste into .env
"""
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

async def main():
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    api_id   = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone    = os.getenv("TELEGRAM_PHONE")

    print(f"\nLogging in to Telegram as {phone}...")
    print("Telegram will send you an SMS code now.\n")

    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        await client.start(phone=phone)
        session_string = client.session.save()

    print("\n" + "="*60)
    print("SUCCESS! Copy this session string into your .env file")
    print("on the line: TELEGRAM_SESSION_STRING=")
    print("="*60)
    print(session_string)
    print("="*60 + "\n")

asyncio.run(main())
