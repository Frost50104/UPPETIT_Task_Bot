# Обработчик команды /admins
from telebot import types
import telebot
import config
from bot_instance import is_admin

def handle_cmnd_admins(bot):
    @bot.message_handler(commands=['admins'])
    def handle_command_admins(message: types.Message):

        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав просматривать список администраторов.")
            return

        """Выводит список администраторов бота."""
        admin_list = []

        for admin_id in config.ADMIN_ID:
            try:
                user = bot.get_chat(admin_id)
                first_name = user.first_name or "Без имени"
                username = f"👤 @{user.username}" if user.username else f"ID: {admin_id}"
                admin_list.append(f"👤 <b>{first_name}</b> ({username})")
            except telebot.apihelper.ApiTelegramException:
                admin_list.append(f"👤 ID: {admin_id} (❌ недоступен)")

        bot.send_message(
            chat_id=message.chat.id,
            text=f"🔹 <b>Список администраторов:</b>\n" + "\n".join(admin_list),
            parse_mode="HTML"
        )