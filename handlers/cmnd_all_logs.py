import os
from logger import get_all_logs

def handle_cmnd_all_logs(bot, is_admin):
    @bot.message_handler(commands=["all_logs"])
    def show_all_logs(message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к логам.", parse_mode="HTML")
            return

        log_data = get_all_logs()
        
        if not log_data:
            bot.send_message(message.chat.id, "📭 Лог пуст.", parse_mode="HTML")
            return

        MAX_LEN = 4000
        if len(log_data) <= MAX_LEN:
            bot.send_message(message.chat.id, f"<b>История всех действий:</b>\n{log_data}", parse_mode="HTML")
        else:
            # Разбиваем на части
            parts = [log_data[i:i + MAX_LEN] for i in range(0, len(log_data), MAX_LEN)]
            bot.send_message(message.chat.id, "<b>История всех действий (разбита на части):</b>", parse_mode="HTML")
            for part in parts:
                bot.send_message(message.chat.id, f"{part}", parse_mode="HTML")