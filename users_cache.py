import json
import telebot
from config import TOKEN, performers

bot = telebot.TeleBot(TOKEN)

def build_user_cache():
    cache = {}
    for group in performers.values():
        for user_id in group:
            uid = str(user_id)
            if uid in cache:
                continue
            try:
                user = bot.get_chat(user_id)
                cache[uid] = {
                    "first_name": user.first_name,
                    "username": user.username
                }
            except Exception as e:
                cache[uid] = {
                    "first_name": None,
                    "username": None,
                    "error": str(e)
                }

    with open("user_cache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)