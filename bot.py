"""Main entry point for Human Telegram Chatbot.
An ultra-realistic, multilingual conversational Telegram bot with zero-key AI,
human typing simulation, sticker & emoji handling, and automated cloud sync
via Telegram channel JSON database.
"""

import os
import sys
import asyncio
import logging
import signal
from collections import defaultdict
from typing import Dict

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from pyrogram.errors import FloodWait

from config import validate_config
from database import TelegramChannelDB
from ai_engine import HumanAIEngine
from sticker_manager import StickerManager
from humanizer import Humanizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("HumanBot")

# Per-user async locks to prevent race conditions and handle rapid messages cleanly
user_locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

class HumanBot:
    def __init__(self):
        valid, conf = validate_config()
        if not valid:
            logger.error(f"Configuration error: {conf}")
            sys.exit(1)

        self.conf = conf
        self.bot_name = conf["BOT_NAME"]
        self.owner_id = conf["OWNER_ID"]
        self.channel_id = conf["DB_CHANNEL_ID"]

        # Initialize Kurigram client
        self.app = Client(
            name="human_bot_session",
            api_id=conf["API_ID"],
            api_hash=conf["API_HASH"],
            bot_token=conf["BOT_TOKEN"],
            workdir="data"
        )

        # Initialize sub-systems
        self.db = TelegramChannelDB(channel_id=self.channel_id, client=self.app)
        self.ai = HumanAIEngine(
            bot_name=self.bot_name,
            gemini_key=conf.get("GEMINI_API_KEY", ""),
            groq_key=conf.get("GROQ_API_KEY", "")
        )
        self.stickers = StickerManager(db=self.db)
        self.sync_task = None
        self._is_running = True

        self._register_handlers()

    def _register_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client: Client, message: Message):
            await self.handle_start(client, message)

        @self.app.on_message(filters.command(["stats", "sync"]) & filters.private)
        async def admin_handler(client: Client, message: Message):
            await self.handle_admin(client, message)

        @self.app.on_message(filters.sticker & (filters.private | filters.mentioned))
        async def sticker_handler(client: Client, message: Message):
            await self.handle_sticker(client, message)

        @self.app.on_message(filters.text & (filters.private | filters.mentioned))
        async def text_handler(client: Client, message: Message):
            await self.handle_text(client, message)

        @self.app.on_message((filters.photo | filters.voice) & filters.private)
        async def media_handler(client: Client, message: Message):
            await self.handle_media(client, message)

    async def handle_start(self, client: Client, message: Message):
        """Warm, human-like welcome greeting (never sounds like an automated bot)."""
        user_id = message.from_user.id
        first_name = message.from_user.first_name or "bhai"
        user = self.db.get_user(user_id)
        user["first_name"] = first_name
        user["username"] = message.from_user.username or ""

        # Reading delay
        await asyncio.sleep(1.2)
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        await asyncio.sleep(1.5)

        greetings = [
            f"Hey {first_name}! Kaisa hai tu? Sab badhiya? Aur bata kya chal raha hai aaj kal! 😊",
            f"Arre {first_name} bhai! Kya haal chal? Kaafi time baad baat ho rahi hai haha. Tu bata kya scene hai?",
            f"Yo {first_name}! Good to see you here. How's everything going with you?"
        ]
        import random
        reply = random.choice(greetings)
        await message.reply_text(reply)
        self.db.add_message_to_history(user_id, "user", message.text or "/start")
        self.db.add_message_to_history(user_id, "assistant", reply)

    async def handle_admin(self, client: Client, message: Message):
        """Admin maintenance commands (stats, manual sync)."""
        if self.owner_id and message.from_user.id != self.owner_id:
            # Pretend not to know any special commands like a real human
            await message.reply_text("Bhai ye kya code bhej raha hai? 😂")
            return

        cmd = message.text.split()[0].lower()
        if "stats" in cmd:
            stats = self.db.data.get("stats", {})
            users_count = len(self.db.data.get("users", {}))
            text = (
                "📊 **Bot Status & Database Overview**\n\n"
                f"👤 **Total Users:** `{users_count}`\n"
                f"💬 **Total Messages:** `{stats.get('total_messages', 0)}`\n"
                f"🎨 **Stickers Handled:** `{stats.get('total_stickers', 0)}`\n"
                f"🕒 **Last Channel Sync:** `{stats.get('last_sync_at', 'None')}`\n"
                f"🚀 **Cloud DB Channel:** `{self.channel_id}`"
            )
            await message.reply_text(text)
        elif "sync" in cmd:
            await message.reply_text("⏳ Syncing database to Telegram channel...")
            await self.db.save_to_channel(force=True)
            await message.reply_text("✅ Sync complete! Latest JSON uploaded and pinned in channel.")

    async def handle_sticker(self, client: Client, message: Message):
        """Handles stickers naturally: learns the sticker and replies with a matching sticker or reaction."""
        user_id = message.from_user.id
        sticker = message.sticker
        chat_id = message.chat.id

        # Learn user sticker
        self.stickers.learn_sticker(sticker.file_id, sticker.emoji)
        self.db.record_sticker()

        async with user_locks[user_id]:
            # Human pause
            await asyncio.sleep(1.2)

            # Option 1: Reply with sticker if available
            reply_sticker = self.stickers.get_sticker_for_emoji(sticker.emoji)
            if reply_sticker:
                try:
                    await client.send_chat_action(chat_id, ChatAction.CHOOSE_STICKER)
                    await asyncio.sleep(1.5)
                    await message.reply_sticker(reply_sticker)
                    return
                except Exception as e:
                    logger.debug(f"Could not send sticker: {e}")

            # Option 2: Reply with emoji reaction
            emoji_reply = self.stickers.get_emoji_response(sticker.emoji or "😂")
            if emoji_reply:
                await client.send_chat_action(chat_id, ChatAction.TYPING)
                await asyncio.sleep(1.8)
                await message.reply_text(emoji_reply)

    async def handle_media(self, client: Client, message: Message):
        """Acknowledges voice notes and photos casually like a real friend."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        import random

        async with user_locks[user_id]:
            await asyncio.sleep(1.5)
            await client.send_chat_action(chat_id, ChatAction.TYPING)
            await asyncio.sleep(2.0)

            if message.photo:
                replies = [
                    "Arre waah, kya photo hai! Mast view hai ekdum 🔥",
                    "Badhiya picture hai bhai! Kaha ki hai ye?",
                    "Mast lag raha hai bro! Ek number pic 👌"
                ]
            else:  # Voice message
                replies = [
                    "Sun raha hu bro, aawaz sahi aa rahi hai haha 👍",
                    "Acha ruko, abhi sunta hu poora audio!",
                    "Arey voice note! Sun liya bhai, mast baat boli tune haha"
                ]
            reply = random.choice(replies)
            await message.reply_text(reply)

    async def handle_text(self, client: Client, message: Message):
        """Primary chat handler: human speed, natural typing action, zero-key AI, anti-flood."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_text = message.text.strip() if message.text else ""

        if not user_text:
            return

        # Ensure orderly, serial handling per user (anti-flood / race condition shield)
        async with user_locks[user_id]:
            try:
                # 1. Update user profile
                user = self.db.get_user(user_id)
                user["first_name"] = message.from_user.first_name or user.get("first_name", "")
                user["username"] = message.from_user.username or user.get("username", "")

                # 2. Check if user sent pure emojis
                emoji_reply = self.stickers.get_emoji_response(user_text)

                # 3. Reading delay (proportional to message length)
                read_delay = Humanizer.calculate_reading_delay(user_text)
                await asyncio.sleep(read_delay)

                # 4. Occasional natural Telegram message reaction (25% chance)
                import random
                if random.random() < 0.28:
                    rxn = self.stickers.get_reaction_emoji(user_text)
                    if rxn:
                        try:
                            await message.react(rxn)
                        except Exception:
                            pass

                # If message was pure emoji, reply with emoji or short comment
                if emoji_reply and len(user_text) <= 4:
                    reply_text = emoji_reply
                else:
                    # 5. Fetch history and generate response
                    history = self.db.get_history(user_id)
                    reply_text = await self.ai.generate_human_reply(user_text, history)

                # 6. Realistic Human Typing Action Simulation
                typing_delay = Humanizer.calculate_typing_delay(reply_text)
                await Humanizer.simulate_human_typing(client, chat_id, typing_delay)

                # 7. Natural Split Message or Single Message
                if Humanizer.should_split_message(reply_text):
                    chunks = Humanizer.split_into_chunks(reply_text)
                    if len(chunks) == 2:
                        # Send first part
                        await message.reply_text(chunks[0])
                        # Quick pause for second message
                        await asyncio.sleep(1.2)
                        await client.send_chat_action(chat_id, ChatAction.TYPING)
                        await asyncio.sleep(1.5)
                        # Send second part
                        await message.reply_text(chunks[1])
                    else:
                        await message.reply_text(reply_text)
                else:
                    await message.reply_text(reply_text)

                # 8. Record in database history
                self.db.add_message_to_history(user_id, "user", user_text)
                self.db.add_message_to_history(user_id, "assistant", reply_text)

            except FloodWait as fw:
                logger.warning(f"Telegram FloodWait encountered: sleeping for {fw.value}s")
                await asyncio.sleep(fw.value)
            except Exception as e:
                logger.error(f"Error handling message from {user_id}: {e}", exc_info=True)
                # Fail gracefully like a real human (e.g. network hiccup)
                try:
                    await asyncio.sleep(1.5)
                    await message.reply_text("Haan bhai? Aawaz nahi aayi/network thoda slow tha, firse bol?")
                except Exception:
                    pass

    async def start(self):
        """Starts the bot client and auto-sync background loop."""
        logger.info("Starting Human Telegram Bot...")
        await self.app.start()

        bot_me = await self.app.get_me()
        logger.info(f"Connected successfully as @{bot_me.username} ({bot_me.first_name})")

        # Initialize and sync database from Telegram channel
        await self.db.init_and_sync()

        # Start periodic database sync background task
        sync_interval = self.conf.get("SYNC_INTERVAL_SECONDS", 300)
        self.sync_task = asyncio.create_task(self.db.start_auto_sync_loop(interval_seconds=sync_interval))

        logger.info("Human Telegram Bot is online and actively chatting!")

        # Keep running until cancelled
        stop_event = asyncio.Event()

        def signal_handler():
            logger.info("Shutdown signal received...")
            stop_event.set()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                pass

        await stop_event.wait()
        await self.stop()

    async def stop(self):
        """Gracefully stops the bot and persists final DB backup to channel."""
        logger.info("Stopping bot and syncing final database state...")
        if self.sync_task:
            self.sync_task.cancel()
        # Final cloud backup upload
        await self.db.save_to_channel(force=True)
        await self.app.stop()
        logger.info("Bot successfully stopped.")

def main():
    bot = HumanBot()
    asyncio.run(bot.start())

if __name__ == "__main__":
    main()
