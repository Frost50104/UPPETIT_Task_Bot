from telebot.types import Message
from users_cache import build_user_cache

def handle_cmnd_update_user_cache(bot, is_admin):
    """Регистрация обработчика команды /update_user_cache"""

    @bot.message_handler(commands=['update_user_cache'])
    def handle_update_user_cache(message: Message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав обновлять кэш.")
            return

        try:
            build_user_cache()
            bot.send_message(message.chat.id, "✅ Кэш пользователей обновлён.")
        except Exception as e:
            bot.send_message(
                message.chat.id,
                f"⚠ Ошибка при обновлении кэша:\n<code>{e}</code>",
                parse_mode="HTML"
            )