import importlib
import config
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def handle_cmnd_auto_send_monthly(bot, is_admin, restart_scheduler):
    """Регистрация обработчиков команды /auto_send_monthly"""

    @bot.message_handler(commands=['auto_send_monthly'])
    def handle_auto_send_monthly(message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять статус ежемесячной рассылки.")
            return

        importlib.reload(config)
        current_status = "✅ Включена" if config.status_monthly == "on" else "⛔ Выключена"
        schedule_list = "\n".join([f"{day}-го числа в {time}" for day, time in config.monthly_schedule])

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="change_monthly_status"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_monthly_status")
        )

        bot.send_message(
            message.chat.id,
            f"📅 <b>Ежемесячное расписание:</b>\n{schedule_list}\n\n"
            f"🔄 <b>Статус рассылки:</b> {current_status}\n\n"
            f"Желаете изменить статус ежемесячной рассылки?",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data in ["change_monthly_status", "cancel_monthly_status"])
    def process_monthly_status_change(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Нет доступа.")
            return

        if call.data == "cancel_monthly_status":
            bot.edit_message_text("❌ Изменение отменено.", call.message.chat.id, call.message.message_id)
            return

        importlib.reload(config)
        new_status = "off" if config.status_monthly == "on" else "on"

        with open("config.py", "r", encoding="utf-8") as file:
            config_content = file.readlines()

        for i, line in enumerate(config_content):
            if line.strip().startswith("status_monthly"):
                config_content[i] = f"status_monthly = '{new_status}'\n"
                break

        with open("config.py", "w", encoding="utf-8") as file:
            file.writelines(config_content)

        importlib.reload(config)
        restart_scheduler()

        new_status_text = "✅ Включена" if new_status == "on" else "⛔ Выключена"
        bot.edit_message_text(f"🔄 Новый статус ежемесячной рассылки: {new_status_text}",
                              call.message.chat.id, call.message.message_id)
