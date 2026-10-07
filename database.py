"""Telegram Channel Database System.
Uses a private Telegram Channel as cloud database storage by uploading and
downloading JSON backups automatically. Zero external database required!
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

LOCAL_DB_FILE = "data/database.json"

class TelegramChannelDB:
    def __init__(self, channel_id: int, client=None):
        self.channel_id = channel_id
        self.client = client
        self.data: Dict[str, Any] = {
            "users": {},
            "stats": {
                "total_messages": 0,
                "total_stickers": 0,
                "total_users": 0,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "last_sync_at": None,
            },
            "meta": {
                "version": "1.0",
                "description": "Human Telegram Bot Cloud Database"
            }
        }
        self.lock = asyncio.Lock()
        self.dirty = False
        self._sync_task: Optional[asyncio.Task] = None
        os.makedirs("data", exist_ok=True)

    def set_client(self, client):
        self.client = client

    async def init_and_sync(self):
        """Loads latest data from Telegram channel or local backup on startup."""
        logger.info(f"Initializing Telegram Channel Database from channel {self.channel_id}...")
        loaded = False

        if self.client:
            try:
                # 1. Try fetching pinned message first
                chat = await self.client.get_chat(self.channel_id)
                pinned = chat.pinned_message
                doc_msg = None

                if pinned and pinned.document and pinned.document.file_name.endswith(".json"):
                    doc_msg = pinned
                    logger.info("Found database backup in pinned message!")
                else:
                    # 2. Search recent messages in the channel for a JSON document
                    async for msg in self.client.get_chat_history(self.channel_id, limit=20):
                        if msg.document and msg.document.file_name.endswith(".json"):
                            doc_msg = msg
                            logger.info(f"Found database backup in message ID {msg.id}")
                            break

                if doc_msg:
                    temp_path = await self.client.download_media(doc_msg)
                    if temp_path and os.path.exists(temp_path):
                        with open(temp_path, "r", encoding="utf-8") as f:
                            content = json.load(f)
                            if isinstance(content, dict) and "users" in content:
                                self.data = content
                                loaded = True
                                logger.info(
                                    f"Successfully synced DB from Telegram Channel! "
                                    f"Users: {len(self.data.get('users', {}))}, "
                                    f"Messages: {self.data.get('stats', {}).get('total_messages', 0)}"
                                )
                        try:
                            os.remove(temp_path)
                        except OSError:
                            pass
            except Exception as e:
                logger.warning(f"Could not load DB from Telegram channel directly: {e}")

        # 3. Fallback to local cache if channel sync didn't find anything
        if not loaded and os.path.exists(LOCAL_DB_FILE):
            try:
                with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    loaded = True
                    logger.info(f"Loaded database from local cache file ({LOCAL_DB_FILE})")
            except Exception as e:
                logger.error(f"Error reading local DB file: {e}")

        if not loaded:
            logger.info("No prior database found. Initialized fresh database schema.")
            self.dirty = True
            # Perform initial upload to channel
            await self.save_to_channel(force=True)

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Gets user profile or creates a default record."""
        uid_str = str(user_id)
        if uid_str not in self.data["users"]:
            self.data["users"][uid_str] = {
                "user_id": user_id,
                "first_name": "",
                "last_name": "",
                "username": "",
                "language_code": "en",
                "joined_at": datetime.now(timezone.utc).isoformat(),
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "messages_count": 0,
                "history": [],
                "memory": {},  # Remembers user facts (e.g. nickname, likes, city)
            }
            self.data["stats"]["total_users"] = len(self.data["users"])
            self.dirty = True
        return self.data["users"][uid_str]

    def update_user(self, user_id: int, user_data: Dict[str, Any]):
        """Updates user record."""
        uid_str = str(user_id)
        self.data["users"][uid_str] = user_data
        self.dirty = True

    def add_message_to_history(self, user_id: int, role: str, content: str, max_history: int = 12):
        """Adds a message to the sliding conversation history."""
        user = self.get_user(user_id)
        user["history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        if len(user["history"]) > max_history:
            user["history"] = user["history"][-max_history:]
        user["messages_count"] = user.get("messages_count", 0) + 1
        user["last_seen"] = datetime.now(timezone.utc).isoformat()
        self.data["stats"]["total_messages"] = self.data["stats"].get("total_messages", 0) + 1
        self.dirty = True

    def get_history(self, user_id: int) -> list:
        """Returns recent conversation history for a user."""
        user = self.get_user(user_id)
        return user.get("history", [])

    def record_sticker(self):
        """Increments sticker count."""
        self.data["stats"]["total_stickers"] = self.data["stats"].get("total_stickers", 0) + 1
        self.dirty = True

    async def save_to_channel(self, force: bool = False):
        """Dumps database to JSON file and uploads to Telegram DB channel."""
        if not self.dirty and not force:
            return

        async with self.lock:
            # 1. Update stats
            now_iso = datetime.now(timezone.utc).isoformat()
            self.data["stats"]["last_sync_at"] = now_iso
            self.data["stats"]["total_users"] = len(self.data.get("users", {}))

            # 2. Write to local file first
            with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

            # 3. Upload to Telegram channel if client is active
            if self.client:
                try:
                    caption = (
                        "💾 **Database Auto-Sync**\n\n"
                        f"👥 **Users:** `{len(self.data.get('users', {}))}`\n"
                        f"💬 **Total Messages:** `{self.data.get('stats', {}).get('total_messages', 0)}`\n"
                        f"🎨 **Stickers Sent:** `{self.data.get('stats', {}).get('total_stickers', 0)}`\n"
                        f"🕒 **Last Sync:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}`\n\n"
                        "⚡ *Status: Fully synced & active.*"
                    )
                    sent_msg = await self.client.send_document(
                        chat_id=self.channel_id,
                        document=LOCAL_DB_FILE,
                        file_name="database.json",
                        caption=caption
                    )
                    # Pin the latest backup message for instant discovery
                    try:
                        await self.client.pin_chat_message(
                            chat_id=self.channel_id,
                            message_id=sent_msg.id,
                            both_sides=False
                        )
                    except Exception:
                        pass

                    self.dirty = False
                    logger.info("Successfully synced database JSON to Telegram channel!")
                except Exception as e:
                    logger.error(f"Failed to upload DB backup to Telegram channel: {e}")

    async def start_auto_sync_loop(self, interval_seconds: int = 300):
        """Periodic background task that automatically syncs DB every N seconds."""
        logger.info(f"Auto-sync loop started. Syncing every {interval_seconds} seconds.")
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                if self.dirty:
                    await self.save_to_channel()
            except asyncio.CancelledError:
                # Flush final backup before cancellation
                await self.save_to_channel(force=True)
                break
            except Exception as e:
                logger.error(f"Error in auto-sync loop: {e}")
