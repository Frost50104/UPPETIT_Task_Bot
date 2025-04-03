import json
import importlib
from telebot.types import Message
import config
from users_cache import build_user_cache

def handle_cmnd_bot_users(bot, is_admin):
    """Регистрация обработчика команды /bot_users"""

    @bot.message_handler(commands=['bot_users'])
    def handle_bot_users(message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав просматривать список пользователей.")
            return

        # Шаг 1 — отправляем предварительное сообщение
        loading_msg = bot.send_message(message.chat.id, "🔁 Обновляем данные пользователей...")

        try:
            # Шаг 2 — обновляем кэш
            from users_cache import build_user_cache
            build_user_cache()

            # Шаг 3 — читаем обновлённый кэш
            with open("user_cache.json", "r", encoding="utf-8") as f:
                user_cache = json.load(f)

            importlib.reload(config)

            # Шаг 4 — формируем сообщение
            response = []

            for group_name, users in config.performers.items():
                user_list = []
                for user_id in users:
                    uid = str(user_id)
                    cached = user_cache.get(uid)
                    if cached:
                        first_name = cached.get("first_name") or "Без имени"
                        username = f"@{cached['username']}" if cached.get("username") else f"ID: {uid}"
                        user_list.append(f"👤 {first_name} ({username})")
                    else:
                        user_list.append(f"⚠ ID: {uid} (не найден в кэше)")

                if user_list:
                    response.append(f"<b>{group_name}</b>:\n" + "\n".join(user_list))
                else:
                    response.append(f"<b>{group_name}</b>:\n 🔹 Нет сотрудников.")

            # Шаг 5 — редактируем сообщение, если оно влезает
            full_text = "\n\n".join(response)
            max_length = 4096

            if len(full_text) <= max_length:
                bot.edit_message_text(full_text, message.chat.id, loading_msg.message_id, parse_mode="HTML")
            else:
                # Если длинное — редактируем первое и продолжаем отправку в новых сообщениях
                bot.edit_message_text("✅ Список пользователей получен.", message.chat.id, loading_msg.message_id)

                # Отправка по частям
                while full_text:
                    part = full_text[:max_length]
                    split_index = part.rfind('\n\n')
                    if split_index == -1 or len(full_text) <= max_length:
                        bot.send_message(message.chat.id, full_text, parse_mode="HTML")
                        break
                    else:
                        part = full_text[:split_index]
                        bot.send_message(message.chat.id, part, parse_mode="HTML")
                        full_text = full_text[split_index:].lstrip()

        except Exception as e:
            bot.edit_message_text(f"⚠ Ошибка при обновлении кэша:\n<code>{e}</code>", message.chat.id,
                                  loading_msg.message_id, parse_mode="HTML")
