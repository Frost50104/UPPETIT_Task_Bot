import importlib
import config
import telebot
import json
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

# 🧠 Глобальный кэш пользователей в памяти
user_cache = {}

def build_user_cache():
    """Перестраивает кэш и сохраняет в файл + память."""
    global user_cache
    importlib.reload(config)
    performers = config.performers  # 🔄 Теперь актуальный performers

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

    user_cache = cache

    with open("user_cache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_user_from_cache(user_id: int):
    """Возвращает информацию о пользователе из кэша."""
    return user_cache.get(str(user_id))