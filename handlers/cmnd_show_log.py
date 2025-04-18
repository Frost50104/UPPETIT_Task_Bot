import os

def handle_cmnd_show_log(bot, is_admin):
    @bot.message_handler(commands=["show_log"])
    def show_log(message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к логам.", parse_mode="HTML")
            return

        log_path = "task_log.txt"
        if not os.path.exists(log_path):
            bot.send_message(message.chat.id, "📭 Лог пуст.", parse_mode="HTML")
            return

        with open(log_path, "r", encoding="utf-8") as f:
            log_data = f.read()

        MAX_LEN = 4000
        if len(log_data) <= MAX_LEN:
            bot.send_message(message.chat.id, f"<b>История действий:</b>\n{log_data}", parse_mode="HTML")
        else:
            # Разбиваем на части
            parts = [log_data[i:i + MAX_LEN] for i in range(0, len(log_data), MAX_LEN)]
            bot.send_message(message.chat.id, "<b>История действий (разбита на части):</b>", parse_mode="HTML")
            for part in parts:
                bot.send_message(message.chat.id, f"{part}", parse_mode="HTML")