import importlib
import config
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def handle_cmnd_auto_send_weekly(bot, is_admin, restart_scheduler):
    """Регистрация обработчиков команды /auto_send_weekly"""

    # ========= Команда /auto_send_weekly =========
    @bot.message_handler(commands=['auto_send_weekly'])
    def handle_auto_send_weekly(message):
        """Показывает статус еженедельной рассылки и предлагает его изменить."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять статус еженедельной рассылки.")
            return

        importlib.reload(config)

        # Перевод дней недели на русский
        day_translate_reverse = {
            "monday": "Понедельник",
            "tuesday": "Вторник",
            "wednesday": "Среда",
            "thursday": "Четверг",
            "friday": "Пятница",
            "saturday": "Суббота",
            "sunday": "Воскресенье"
        }

        schedule_list = "\n".join([
            f"{day_translate_reverse.get(day, day)} в {time}"
            for day, time in config.weekly_schedule
        ])

        current_status = "✅ Включена" if config.status_weekly == "on" else "⛔ Выключена"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="change_weekly_status"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_weekly_status")
        )

        bot.send_message(
            message.chat.id,
            f"📅 <b>Недельное расписание:</b>\n{schedule_list}\n\n"
            f"🔄 <b>Статус еженедельной рассылки:</b> {current_status}\n\n"
            f"Желаете изменить статус еженедельной рассылки?",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # ========= Обработка переключателя /auto_send_weekly =========
    @bot.callback_query_handler(func=lambda call: call.data in ["change_weekly_status", "cancel_weekly_status"])
    def process_weekly_status_change(call):
        """Обрабатывает переключение статуса еженедельной рассылки."""
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав изменять статус.")
            return

        if call.data == "cancel_weekly_status":
            bot.edit_message_text("❌ Изменение отменено.", call.message.chat.id, call.message.message_id)
            return

        importlib.reload(config)
        new_status = "off" if config.status_weekly == "on" else "on"

        # Обновляем config.py
        with open("config.py", "r", encoding="utf-8") as file:
            config_content = file.readlines()

        for i, line in enumerate(config_content):
            if line.strip().startswith("status_weekly"):
                config_content[i] = f"status_weekly = '{new_status}'\n"
                break

        with open("config.py", "w", encoding="utf-8") as file:
            file.writelines(config_content)

        importlib.reload(config)
        restart_scheduler()

        new_status_text = "✅ Включена" if new_status == "on" else "⛔ Выключена"
        bot.edit_message_text(f"🔄 Новый статус еженедельной рассылки: {new_status_text}",
                              call.message.chat.id, call.message.message_id)