
import importlib
import config
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def handle_cmnd_auto_send(bot, is_admin, restart_scheduler):
    """Регистрация обработчиков команды /auto_send"""

    # ========= Команда /auto_send =========
    @bot.message_handler(commands=['auto_send'])
    def handle_auto_send(message):
        """Показывает текущий статус автоматической рассылки задач и позволяет изменить его."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять статус автоматической рассылки.")
            return

        # Перезагружаем config.py перед выводом информации
        importlib.reload(config)

        current_status = "✅ Включена" if config.status_work_time == "on" else "⛔ Выключена"
        schedule_list = "\n".join(config.work_time)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="change_auto_send"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_auto_send")
        )

        bot.send_message(
            message.chat.id,
            f"📅 *Текущее расписание автоматической рассылки:*\n{schedule_list}\n\n"
            f"🔄 *Статус автоматической рассылки:* {current_status}\n\n"
            f"Желаете изменить статус автоматической рассылки?",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # ========= Обработка нажатий "Да" / "Нет" =========
    @bot.callback_query_handler(func=lambda call: call.data in ["change_auto_send", "cancel_auto_send"])
    def process_auto_send_change(call):
        """Переключает статус автоматической рассылки."""
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав изменять статус автоматической рассылки.")
            return

        if call.data == "cancel_auto_send":
            bot.edit_message_text("❌ Изменение отменено.", call.message.chat.id, call.message.message_id)
            return

        # Перезагружаем config.py перед изменением
        importlib.reload(config)

        new_status = "off" if config.status_work_time == "on" else "on"

        # Читаем config.py
        config_file = "config.py"
        with open(config_file, "r", encoding="utf-8") as file:
            config_content = file.readlines()

        # Обновляем `status_work_time`
        for i, line in enumerate(config_content):
            if line.strip().startswith("status_work_time"):
                config_content[i] = f"status_work_time = '{new_status}'\n"
                break

        # Записываем обновленный config.py
        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(config_content)

        # Перезагружаем config.py для применения изменений
        importlib.reload(config)

        # Перезапускаем автоматическую рассылку
        restart_scheduler()

        new_status_text = "✅ Включена" if new_status == "on" else "⛔ Выключена"
        bot.edit_message_text(f"🔄 Новый статус автоматической рассылки: {new_status_text}",
                              call.message.chat.id, call.message.message_id)
