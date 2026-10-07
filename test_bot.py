"""Comprehensive test suite for Human Telegram Bot components."""

import asyncio
import os
import shutil

from ai_engine import HumanAIEngine
from sticker_manager import StickerManager
from humanizer import Humanizer
from database import TelegramChannelDB

async def run_tests():
    print("========================================")
    print("🧪 Testing Human Telegram Bot Components")
    print("========================================")

    # 1. Test Humanizer
    print("\n--- 1. Testing Humanizer ---")
    read_delay = Humanizer.calculate_reading_delay("bhai kya kar raha hai?")
    print(f"Reading delay for short msg: {read_delay:.2f}s")
    assert 0.8 <= read_delay <= 3.5

    typing_delay = Humanizer.calculate_typing_delay("bas chill kar raha hu bro")
    print(f"Typing delay for response: {typing_delay:.2f}s")
    assert 1.5 <= typing_delay <= 7.0

    split_test = Humanizer.split_into_chunks("Arre waah! Kal hi toh baat kar rahe the ispe haha")
    print(f"Split test result: {split_test}")
    print("✅ Humanizer tests passed!")

    # 2. Test Sticker & Emoji Manager
    print("\n--- 2. Testing Sticker & Emoji Manager ---")
    sm = StickerManager()
    sm.learn_sticker("test_file_id_123", "😂")
    retrieved = sm.get_sticker_for_emoji("😂")
    print(f"Learned & retrieved sticker for 😂: {retrieved}")
    assert retrieved == "test_file_id_123"

    emoji_reply = sm.get_emoji_response("😂😂")
    print(f"Emoji reaction for 😂: {emoji_reply}")
    assert emoji_reply is not None

    reaction_emoji = sm.get_reaction_emoji("bhai tu mast hai haha")
    print(f"Message reaction for text: {reaction_emoji}")
    assert reaction_emoji in ["😂", "❤️", "👍", "🔥"]
    print("✅ Sticker & Emoji tests passed!")

    # 3. Test Database JSON Serialization & Sliding History
    print("\n--- 3. Testing Database System ---")
    test_db = TelegramChannelDB(channel_id=-1001234567890)
    user = test_db.get_user(987654321)
    assert user["user_id"] == 987654321

    test_db.add_message_to_history(987654321, "user", "Kaisa hai?")
    test_db.add_message_to_history(987654321, "assistant", "Badhiya bhai!")
    history = test_db.get_history(987654321)
    assert len(history) == 2
    print(f"History recorded: {history}")

    await test_db.save_to_channel(force=True)
    assert os.path.exists("data/database.json")
    print("Local database.json created successfully!")
    print("✅ Database tests passed!")

    # 4. Test AI Engine (Multilingual & Anti-bot persona)
    print("\n--- 4. Testing AI Engine ---")
    ai = HumanAIEngine(bot_name="Alex")

    # Test Bot suspicion
    bot_reply = await ai.generate_human_reply("bhai tu bot hai kya?")
    print(f"Q: bhai tu bot hai kya?\nA: {bot_reply}")
    assert not any(phrase in bot_reply.lower() for phrase in ["i am an ai", "i am a bot", "language model", "virtual assistant"])

    # Test Hinglish
    hinglish_reply = await ai.generate_human_reply("aur bhai weekend ka kya scene hai?")
    print(f"Q: aur bhai weekend ka kya scene hai?\nA: {hinglish_reply}")
    assert len(hinglish_reply) > 2

    # Test Hindi
    hindi_reply = await ai.generate_human_reply("भाई आज का क्या प्लान है?")
    print(f"Q: भाई आज का क्या प्लान है?\nA: {hindi_reply}")
    assert len(hindi_reply) > 2

    # Test English
    eng_reply = await ai.generate_human_reply("Hey, what are you doing right now?")
    print(f"Q: Hey, what are you doing right now?\nA: {eng_reply}")
    assert len(eng_reply) > 2
    print("✅ AI Engine tests passed!")

    print("\n========================================")
    print("🎉 ALL COMPONENT TESTS PASSED SUCCESSFULLY!")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
