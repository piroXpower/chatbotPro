#!/bin/bash
# One-click startup script for Human Telegram Chatbot

cd "$(dirname "$0")"

echo "==============================================="
echo "   🤖 Human Telegram Bot - Launching...       "
echo "==============================================="

if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Creating from sample.env..."
    cp sample.env .env
    echo "❗ Please edit .env with your BOT_TOKEN, API_ID, API_HASH, and DB_CHANNEL_ID."
    echo "Then re-run: ./start.sh"
    exit 1
fi

# Check venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "📥 Installing dependencies..."
    ./venv/bin/pip install -r requirements.txt
fi

echo "🚀 Starting HumanBot..."
exec ./venv/bin/python bot.py
