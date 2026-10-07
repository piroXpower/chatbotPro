# 🤖 RealHuman Telegram Chatbot (अल्ट्रा-रियलिस्टिक ह्यूमन बॉट)

An ultra-realistic, conversational Telegram bot that speaks **Hindi**, **Hinglish**, **English**, and many other languages like a genuine human friend. 

It **never** admits or sounds like a bot, matches natural human reply speeds, sends live `typing...` indicators, reacts with stickers and emojis, never spams or broadcasts, and uses a **Telegram Channel as its cloud database** (JSON auto-sync) with zero setup headaches!

---

## ✨ Features

- 👤 **100% Real Human Persona**:
  - Never uses corporate AI disclaimers (*"As an AI..."*, *"How can I help you today?"*).
  - If asked *"Are you a bot?"*, it laughs it off casually:
    > *"Abe pagal hai kya? Insaan hu main bhai 😂 Robot hota toh yaha chill thodi kar raha hota!"*
  - Casual punctuation, natural abbreviations, and friendly Indian / global vibe.

- 🌐 **Multilingual Mastery (Hindi, English, Hinglish & More)**:
  - Dynamically mirrors the user's language:
    - **Hinglish**: *"Bas badhiya bro, tu bata kya scene hai sham ka?"*
    - **Hindi (Devanagari)**: *"नमस्ते भाई! सब ठीक-ठाक है, तुम बताओ क्या चल रहा है?"*
    - **English**: *"Hey man! Just chilling with a cup of coffee. What's up with you?"*
    - **Any Other Language**: Bengali, Marathi, Punjabi, Tamil, Telugu, Spanish, French, etc.

- ⚡ **Requires ONLY 4 Telegram Credentials (Nothing Else!)**:
  - `BOT_TOKEN` (from [@BotFather](https://t.me/BotFather))
  - `API_ID` (from [my.telegram.org](https://my.telegram.org))
  - `API_HASH` (from [my.telegram.org](https://my.telegram.org))
  - `DB_CHANNEL_ID` (Telegram Channel ID where database JSON is automatically synced)
  - **Zero External Database**: No MongoDB, MySQL, PostgreSQL, or Redis required.
  - **Zero Paid AI Key Required**: Powered out of the box by high-speed Zero-Key AI + offline human conversational engine.

- ⏱️ **Human Reply Speed & Live Typing Action**:
  - Simulates natural reading delays (0.8s – 2.5s) based on user's message length.
  - Emits real Telegram `typing...` (`ChatAction.TYPING`) continuously while thinking and typing.
  - Types at realistic human speed (25–35 chars/sec) instead of instant robotic blasts.
  - **Natural Message Splitting**: Occasionally sends two short consecutive texts (*"Arre waah!"* ...typing... *"Maine bhi dekha tha wo haha"*) just like real texting friends do.

- 🎨 **Stickers & Emoji Reactions**:
  - Recognizes user stickers and automatically maps emotions.
  - **Self-Learning Sticker Pool**: Organically remembers user stickers and replies with matching fun stickers.
  - Drops Telegram emoji reactions (👍, ❤️, 😂, 🔥) on messages.
  - Responds to emojis with expressive human reactions.

- 🛡️ **Anti-Flood, Anti-Spam & Strictly No Broadcast**:
  - Serial queue per user so concurrent messages are handled smoothly without race conditions.
  - Catches Telegram `FloodWait` gracefully.
  - Never spams advertisements, broadcast messages, or unsolicited notifications.

- ☁️ **Telegram Channel Cloud Database (Auto-Sync & Self-Healing)**:
  - Automatically uploads `database.json` to your private Telegram channel.
  - **Auto-Sync on Startup**: Reads and restores user profiles and history directly from the pinned channel backup on launch.
  - **Periodic Auto-Save**: Backs up memory state to the channel every 5 minutes and upon shutdown.
  - *"No tention of starting and doing something"* — completely autonomous and self-healing!

---

## 📁 Project Structure

```
human_telegram_bot/
├── config.py             # Validates & loads Telegram credentials
├── database.py           # Telegram Channel Cloud Database engine (JSON sync)
├── ai_engine.py          # Multilingual AI engine (Zero-Key + Human Fallbacks)
├── humanizer.py          # Typing delay calculators & ChatAction loop
├── sticker_manager.py    # Telegram stickers and emoji reactions engine
├── bot.py                # Main bot runner with Kurigram event handlers
├── sample.env            # Template configuration file
├── requirements.txt      # Lightweight production dependencies
├── start.sh              # One-click startup shell script
├── test_bot.py           # Comprehensive component verification test
├── Dockerfile            # Container deployment support
└── docker-compose.yml    # Docker Compose configuration
```

---

## 🚀 Quick Setup Guide

### 1. Requirements
- Python 3.10+ (tested up to Python 3.14)
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- An `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org)
- A private Telegram Channel where your bot is added as **Administrator**

### 2. Configure Credentials
Copy `sample.env` to `.env`:
```bash
cp sample.env .env
```

Edit `.env` with your values:
```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
DB_CHANNEL_ID=-1001234567890
```

> **How to get your `DB_CHANNEL_ID`:**
> 1. Create a private Telegram Channel (e.g. *"MyBot Cloud DB"*).
> 2. Add your bot as an **Administrator** with permission to send & pin messages.
> 3. Forward any message from the channel to [@userinfobot](https://t.me/userinfobot) or [@MissRose_bot](https://t.me/MissRose_bot) to get the ID (it will start with `-100`).

### 3. Launch the Bot

Using the one-click script:
```bash
chmod +x start.sh
./start.sh
```

Or manually:
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python3 bot.py
```

### 4. Docker Deployment (Optional)
```bash
docker compose up -d
```

---

## 🧪 Testing Subsystems
You can run the built-in test suite anytime to verify AI prompt handling, sticker learning, database JSON generation, and humanizer timings:
```bash
./venv/bin/python test_bot.py
```

---

## 🛠️ Admin Commands
When chatting with your bot from your `OWNER_ID` account:
- `/stats`: Shows live database statistics (total users, message count, stickers handled, last sync).
- `/sync`: Immediately creates and pins a fresh `database.json` backup in your Telegram channel.
