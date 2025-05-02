import os
from logger import get_all_logs, ALL_LOGS_FILE

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

        # Отправляем файл с логами
        with open(ALL_LOGS_FILE, 'rb') as log_file:
            bot.send_document(
                message.chat.id, 
                log_file, 
                caption="<b>История всех действий</b>", 
                parse_mode="HTML"
            )
