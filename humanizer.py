"""Humanizer Engine for Telegram Chatbot.
Simulates realistic human reading time, typing action loops, jitter,
natural message splitting, and anti-flood pacing.
"""

import asyncio
import random
import logging
from typing import List
from pyrogram.enums import ChatAction

logger = logging.getLogger(__name__)

class Humanizer:
    @staticmethod
    def calculate_reading_delay(incoming_text: str) -> float:
        """Calculates realistic time a human takes to read an incoming message."""
        length = len(incoming_text)
        # Base read delay: 0.8s to 2.5s based on length with random jitter
        delay = 0.8 + (length * 0.02) + random.uniform(0.2, 0.8)
        return min(delay, 3.0)

    @staticmethod
    def calculate_typing_delay(outgoing_text: str) -> float:
        """Calculates realistic human typing delay based on reply length."""
        length = len(outgoing_text)
        # Human typing speed approx 25-35 chars per sec + thinking pause
        delay = 1.5 + (length * 0.04) + random.uniform(0.3, 1.2)
        return min(max(delay, 1.8), 6.5)

    @staticmethod
    async def simulate_human_typing(client, chat_id: int, duration: float):
        """Continuously sends Telegram 'typing...' action during the delay."""
        elapsed = 0.0
        interval = 4.0  # Telegram typing action expires after 5 seconds

        while elapsed < duration:
            try:
                await client.send_chat_action(chat_id, ChatAction.TYPING)
            except Exception as e:
                logger.debug(f"Could not send typing action: {e}")
                break

            sleep_time = min(interval, duration - elapsed)
            await asyncio.sleep(sleep_time)
            elapsed += sleep_time

    @staticmethod
    def should_split_message(text: str) -> bool:
        """Determines if a message looks more natural split into two short messages."""
        if len(text) < 35 or len(text) > 160:
            return False
        # Split on sentence boundaries if 2 short sentences exist
        if any(punct in text for punct in ["! ", "? ", ". "]):
            # 25% chance to split for organic human feeling
            return random.random() < 0.28
        return False

    @staticmethod
    def split_into_chunks(text: str) -> List[str]:
        """Splits a response into two natural conversational chunks."""
        for sep in ["! ", "? ", ". "]:
            if sep in text:
                parts = text.split(sep, 1)
                first = parts[0].strip() + sep.strip()
                second = parts[1].strip()
                if first and second and len(first) > 3 and len(second) > 3:
                    return [first, second]
        return [text]
