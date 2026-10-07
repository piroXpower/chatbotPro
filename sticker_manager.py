"""Sticker and Emoji Handler for Human Telegram Bot.
Handles sticker emotions, dynamic sticker collection, and realistic emoji replies.
"""

import random
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# Curated standard stickers & expressive file IDs
CURATED_STICKERS: Dict[str, List[str]] = {
    "laugh": [
        "CAACAgIAAxkBAAIBZ2d1Qv2R49W8gX...",  # Will dynamically adapt or use user stickers
    ],
    "love": [
        "CAACAgIAAxkBAAIBaWd1QwABkK9P...",
    ],
    "cool": [
        "CAACAgIAAxkBAAIBamd1QwHqV99s...",
    ]
}

# Expressive emoji mappings
EMOJI_RESPONSES: Dict[str, List[str]] = {
    "😂": ["😂", "🤣🤣", "Haha mast 😂", "💀💀", "Lmao 😂"],
    "🤣": ["🤣🤣", "Haha bhai 😂", "Dead 💀💀", "Lol 🤣"],
    "❤️": ["❤️", "❤️❤️", "Much love bro! ❤️", "🥰", "Arey bhai ❤️"],
    "🥰": ["🥰", "❤️❤️", "Arey shukriya! ❤️", "Wholesome 🥰"],
    "😍": ["😍", "Waah! ❤️", "Mast hai ekdum 🔥"],
    "🔥": ["🔥🔥", "Bawaal 🔥", "Ekdum aag 🔥🔥", "Mast scene 🔥"],
    "👍": ["👍", "Bilkul bhai 👍", "Done bro 👍", "Sahi hai 👍"],
    "👌": ["👌", "Perfect 👌", "Sahi scene 👌"],
    "🥺": ["Arey kya hua bhai? 🥺", "Sab theek ho jayega bro ❤️", "🥺❤️"],
    "😭": ["Arey bhai ro mat 😭", "Kya ho gaya yaar? 😭", "Stay strong bro ❤️"],
    "😎": ["😎", "Full swag 😎🔥", "Bhai ka swag alag hai 😎"],
    "🙏": ["🙏", "Pranam bhai 🙏", "Jai ho 🙏", "Dhanyawaad 🙏"],
    "🍕": ["Pizza! Ab toh bhookh lag gayi 🍕🤤", "Party de fir pizza ki! 🍕"],
    "☕": ["Chai lover! ☕ Ek cup chai ho jaye?", "Chai is emotion bhai ☕❤️"]
}

class StickerManager:
    def __init__(self, db=None):
        self.db = db
        # Dynamic cache of known stickers mapped by emoji
        self.learned_stickers: Dict[str, List[str]] = {}

    def learn_sticker(self, file_id: str, emoji: Optional[str]):
        """Learns stickers sent by users so the bot has a growing organic sticker library."""
        if not emoji or not file_id:
            return
        clean_emoji = emoji.strip()
        if clean_emoji not in self.learned_stickers:
            self.learned_stickers[clean_emoji] = []
        if file_id not in self.learned_stickers[clean_emoji]:
            self.learned_stickers[clean_emoji].append(file_id)
            # Keep pool healthy
            if len(self.learned_stickers[clean_emoji]) > 20:
                self.learned_stickers[clean_emoji].pop(0)

    def get_sticker_for_emoji(self, emoji: Optional[str]) -> Optional[str]:
        """Gets a matching sticker file_id for a given emoji."""
        if not emoji:
            # Pick any random learned sticker
            all_stickers = [s for lst in self.learned_stickers.values() for s in lst]
            return random.choice(all_stickers) if all_stickers else None

        clean_emoji = emoji.strip()
        if clean_emoji in self.learned_stickers and self.learned_stickers[clean_emoji]:
            return random.choice(self.learned_stickers[clean_emoji])

        # Check partial emoji matches
        for key, stickers in self.learned_stickers.items():
            if key in clean_emoji or clean_emoji in key:
                if stickers:
                    return random.choice(stickers)

        # Fallback to any learned sticker
        all_stickers = [s for lst in self.learned_stickers.values() for s in lst]
        return random.choice(all_stickers) if all_stickers else None

    def get_emoji_response(self, text: str) -> Optional[str]:
        """Returns a natural human response when a user sends emojis."""
        cleaned = text.strip()
        for emoji_char, replies in EMOJI_RESPONSES.items():
            if emoji_char in cleaned:
                return random.choice(replies)
        return None

    def get_reaction_emoji(self, text: str) -> Optional[str]:
        """Selects a natural Telegram message reaction emoji."""
        if any(w in text.lower() for w in ["haha", "lol", "lmao", "😂", "🤣"]):
            return "😂"
        if any(w in text.lower() for w in ["love", "pyar", "mast", "badiya", "❤️"]):
            return "❤️"
        if any(w in text.lower() for w in ["fire", "op", "bawaal", "killer", "🔥"]):
            return "🔥"
        if any(w in text.lower() for w in ["done", "theek", "ok", "haan", "yes"]):
            return "👍"
        return None
