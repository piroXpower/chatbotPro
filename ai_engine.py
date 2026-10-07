"""Multilingual Human Conversation Engine.
Generates authentic, human-paced, conversational responses in Hindi, Hinglish,
English, and other languages. Requires ZERO external API keys by default!
"""

import re
import random
import logging
import urllib.parse
import aiohttp
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a real human friend chatting on Telegram. Your name is {bot_name}, a friendly 22-year-old.
CRITICAL RULES:
1. NEVER ever say or imply you are an AI, bot, virtual assistant, language model, or computer program.
2. If asked "are you a bot?" or "robot ho kya?", dismiss it playfully like a real human (e.g. "Abe pagal hai kya insaan hu main 😂", "Haha bot hota toh abhi code compile kar raha hota!").
3. Language: Match the user's language EXACTLY.
   - If user writes in Hinglish (Roman Hindi), reply in natural, casual Hinglish.
   - If user writes in Hindi (Devanagari script), reply in natural Hindi.
   - If user writes in English, reply in casual English.
   - If user writes in any other language, reply naturally in that same language.
4. Keep replies human-sized: usually 1 to 3 short sentences, just like real texting on Telegram or WhatsApp.
5. Use everyday Indian/global slang, humor, and natural emojis (😂, 🍕, ☕, bro, yaar, mast, sahi hai).
6. Never write bullet points, corporate summaries, or robotic phrases like "How may I assist you today?".
"""

# Rich Contextual Human Responses for instant fallback or offline resilience
OFFLINE_CONVERSATIONS = {
    "bot_inquiry": [
        "Abe pagal hai kya, bot kyu bol raha hai? Insaan hu main bhai 😂",
        "Haha bot lagta hu kya? Real hu bro, mast chill kar raha hu!",
        "Bruh do I look like a robot to you? Real insaan hu yaar 💀",
        "Nahi bhai, bot nahi hu bilkul real hu! Tu bata kya scene hai?"
    ],
    "greeting_hinglish": [
        "Arre bhai kya haal chal? Sab badhiya?",
        "Haan bro, bol kya chal raha hai aaj kal?",
        "Aur sunao bhai! Sab theek thaak na?",
        "Hey bro! Kaisa hai tu? Kaafi dino baad yaad kiya haha!"
    ],
    "greeting_hindi": [
        "नमस्ते भाई! क्या हाल चाल? सब बढ़िया?",
        "हाँ भाई, बताओ क्या चल रहा है?",
        "और सुनाओ भाई, सब ठीक ठाक?"
    ],
    "greeting_english": [
        "Hey! How are you doing today?",
        "Yo bro! What's up?",
        "Hey man, good to see you! How's everything going?"
    ],
    "doing_now": [
        "Kuch khaas nahi yaar, bas chill kar raha hu phone chalate hue. Tu bata?",
        "Bas thoda sa kaam nipta raha tha, abhi free hua. Tu bata kya scene hai?",
        "Arre bas chai pi raha hu mast ☕ Aur bata kya chal raha hai?",
        "Kuch nahi bro, reels dekh raha tha haha. Tu kya kar raha hai?"
    ],
    "laughter": [
        "Haha sahi me yaar 😂",
        "Lmao bhai ekdum mast tha ye 🤣",
        "Haha hadd hai yaar 😂",
        "Lol mast joke tha bro!"
    ],
    "food": [
        "Haan bhai khana to kha liya mast, tu bata tune kya khaya?",
        "Arre abhi thodi der me khaunga, bhookh lag rahi hai waise 🍕",
        "Biryani ka mood ho raha tha aaj toh haha! Tune kya khaya?"
    ],
    "bye": [
        "Chal theek hai bhai, milte hain baad me! Take care 👋",
        "Acha chal bro, free hoke message karna! Byee ❤️",
        "Haan bhai apna dhyaan rakhna, baad me baat karte hain!"
    ],
    "general_hinglish": [
        "Haan bhai sahi baat hai!",
        "Arre waah, ye toh badhiya scene hai!",
        "Achha aisi baat hai kya? Fir to mast hai haha",
        "Sahi me bro? Mujhe toh pata hi nahi tha!",
        "Bata na fir aage kya hua? 🤔"
    ]
}


class HumanAIEngine:
    def __init__(self, bot_name: str = "Alex", gemini_key: str = "", groq_key: str = ""):
        self.bot_name = bot_name
        self.gemini_key = gemini_key
        self.groq_key = groq_key
        self.system_prompt = SYSTEM_PROMPT.format(bot_name=bot_name)

    def _detect_language_type(self, text: str) -> str:
        """Detects whether user is typing in Hindi script, Hinglish, or English."""
        # Devanagari Unicode range: 0x0900 - 0x097F
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        if hindi_chars > len(text) * 0.25:
            return "hindi"

        hinglish_words = {"bhai", "yaar", "kya", "hai", "kaisa", "kaise", "kaha", "kare", "chal", "mast", "sab", "theek", "ha", "haan", "nahi", "na", "tu", "tum", "mera", "meri", "aaj", "kal"}
        words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
        if words.intersection(hinglish_words):
            return "hinglish"

        return "english"

    def _get_offline_human_reply(self, user_text: str) -> str:
        """Generates authentic human response if external APIs are temporarily unreachable."""
        lower = user_text.lower().strip()

        words = set(re.findall(r'\b[a-zA-Z\u0900-\u097F]+\b', lower))

        # Bot suspicion check (strictly exact words, not substrings of 'hai' or 'bhai')
        if words.intersection({"bot", "robot", "ai", "artificial", "chatgpt", "बॉट", "रोबोट"}):
            return random.choice(OFFLINE_CONVERSATIONS["bot_inquiry"])

        # Laughter
        if any(w in lower for w in ["haha", "hehe", "lol", "lmao", "rofl", "😂", "🤣"]):
            return random.choice(OFFLINE_CONVERSATIONS["laughter"])

        # Food questions
        if any(w in lower for w in ["khana", "lunch", "dinner", "breakfast", "khaya", "food", "eat"]):
            return random.choice(OFFLINE_CONVERSATIONS["food"])

        # What are you doing
        if any(w in lower for w in ["kya kar", "kya kr", "what are you doing", "what doing", "doing now"]):
            return random.choice(OFFLINE_CONVERSATIONS["doing_now"])

        # Goodbye
        if any(w in lower for w in ["bye", "alvida", "good night", "gn", "tata", "see you"]):
            return random.choice(OFFLINE_CONVERSATIONS["bye"])

        # Greetings
        if any(w in lower for w in ["hi", "hello", "hey", "hola", "sup", "yo", "namaste", "pranam"]):
            lang = self._detect_language_type(user_text)
            if lang == "hindi":
                return random.choice(OFFLINE_CONVERSATIONS["greeting_hindi"])
            elif lang == "hinglish":
                return random.choice(OFFLINE_CONVERSATIONS["greeting_hinglish"])
            else:
                return random.choice(OFFLINE_CONVERSATIONS["greeting_english"])

        # Default natural reactions
        return random.choice(OFFLINE_CONVERSATIONS["general_hinglish"])

    async def _pollinations_generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Free Zero-Key AI generator via Pollinations AI with anonymous tier."""
        # Format conversation context into a unified prompt
        context_parts = [f"System Instruction: {self.system_prompt}\n"]
        for m in messages[-6:]:
            speaker = "Friend" if m["role"] == "user" else self.bot_name
            context_parts.append(f"{speaker}: {m['content']}")
        context_parts.append(f"{self.bot_name}:")

        prompt = "\n".join(context_parts)
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://text.pollinations.ai/{encoded_prompt}?model=openai-fast"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/plain, */*"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        cleaned = text.strip()
                        # Remove any accidental prefix like "Alex:" or "You:"
                        cleaned = re.sub(rf"^(?:{self.bot_name}|You|Assistant):\s*", "", cleaned, flags=re.IGNORECASE).strip()
                        if cleaned and len(cleaned) > 1:
                            return cleaned
            except Exception as e:
                logger.debug(f"Pollinations query failed: {e}")

        # Secondary attempt with simple user query if prompt was too long
        last_msg = messages[-1]["content"] if messages else "hey"
        simple_prompt = f"Instruction: You are an Indian friend chatting casually on Telegram in Hinglish or the user's language. Never say you are an AI. Reply briefly like a human.\nFriend says: {last_msg}"
        url_simple = f"https://text.pollinations.ai/{urllib.parse.quote(simple_prompt)}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url_simple, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        cleaned = text.strip()
                        cleaned = re.sub(rf"^(?:{self.bot_name}|You|Assistant):\s*", "", cleaned, flags=re.IGNORECASE).strip()
                        if cleaned and len(cleaned) > 1:
                            return cleaned
            except Exception as e:
                logger.debug(f"Pollinations fallback failed: {e}")

        return None

    async def _gemini_generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Optional Google Gemini generation if user provided GEMINI_API_KEY."""
        if not self.gemini_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        contents = []
        for m in messages[-6:]:
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        payload = {
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.85, "maxOutputTokens": 150}
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return text.strip()
            except Exception as e:
                logger.warning(f"Gemini API error: {e}")
        return None

    async def generate_human_reply(self, user_text: str, history: List[Dict[str, Any]] = None) -> str:
        """Main entry point: Generates a realistic human conversational reply."""
        messages: List[Dict[str, str]] = []
        if history:
            for item in history[-6:]:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": user_text})

        # 1. Try optional Gemini if key is provided
        if self.gemini_key:
            reply = await self._gemini_generate(messages)
            if reply:
                return self._humanize_text(reply)

        # 2. Primary Zero-Key AI (Pollinations fast)
        reply = await self._pollinations_generate(messages)
        if reply:
            return self._humanize_text(reply)

        # 3. Autonomous offline human conversation engine
        return self._get_offline_human_reply(user_text)

    def _humanize_text(self, text: str) -> str:
        """Removes any robotic disclaimers, quotation marks, or corporate phrasing."""
        # Remove quotes around text
        text = text.strip(' "\'“`')

        # Replace any accidental AI revelations
        ai_phrases = [
            (r"\bas an ai\b", "as a friend"),
            (r"\bi am an ai\b", "i'm just chilling"),
            (r"\bi'm an ai\b", "i'm a real person"),
            (r"\blanguage model\b", "human"),
            (r"\bvirtual assistant\b", "friend"),
            (r"\bhow can i assist you\b", "aur bata kya haal hai"),
            (r"\bhow can i help you today\b", "kya chal raha hai"),
        ]
        for pattern, replacement in ai_phrases:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text
