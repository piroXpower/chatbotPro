"""Configuration management for Human Telegram Chatbot.
Loads settings from .env file or environment variables.
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Required Telegram Credentials
API_ID_RAW = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_CHANNEL_ID_RAW = os.getenv("DB_CHANNEL_ID")

# Optional Fallback AI Keys (100% optional - bot works without any keys!)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Bot Personality & Humanizer Settings
BOT_NAME = os.getenv("BOT_NAME", "Alex")
OWNER_ID_RAW = os.getenv("OWNER_ID", "0")

# Auto-sync interval in seconds (default 300 seconds = 5 minutes)
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "300"))

# Validate required variables
def validate_config():
    missing = []
    if not API_ID_RAW:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not DB_CHANNEL_ID_RAW:
        missing.append("DB_CHANNEL_ID")

    if missing:
        return False, f"Missing required environment variables: {', '.join(missing)}"

    try:
        api_id = int(API_ID_RAW)
    except ValueError:
        return False, "API_ID must be a valid integer."

    try:
        channel_id = int(DB_CHANNEL_ID_RAW)
        # Ensure channel_id has -100 prefix if it is a supergroup/channel ID
        if channel_id > 0:
            channel_id = -int(f"100{channel_id}")
    except ValueError:
        return False, "DB_CHANNEL_ID must be an integer (e.g. -1001234567890)."

    try:
        owner_id = int(OWNER_ID_RAW) if OWNER_ID_RAW else 0
    except ValueError:
        owner_id = 0

    return True, {
        "API_ID": api_id,
        "API_HASH": API_HASH.strip(),
        "BOT_TOKEN": BOT_TOKEN.strip(),
        "DB_CHANNEL_ID": channel_id,
        "OWNER_ID": owner_id,
        "BOT_NAME": BOT_NAME.strip(),
        "SYNC_INTERVAL_SECONDS": SYNC_INTERVAL_SECONDS,
        "GEMINI_API_KEY": GEMINI_API_KEY.strip(),
        "GROQ_API_KEY": GROQ_API_KEY.strip()
    }
