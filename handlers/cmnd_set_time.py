import re
import importlib
import config
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def handle_cmnd_set_time(bot, is_admin, restart_scheduler):
    """Регистрация обработчиков команды /set_time"""

    # ========= Команда /set_time =========
    @bot.message_handler(commands=['set_time'])
    def handle_set_time(message):
        """Запрашивает у администратора изменение времени отправки заданий."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять время отправки заданий.")
            return

        # Вывод текущего расписания
        current_schedule = "\n".join(config.work_time)
        current_status = "✅ Включена" if config.status_work_time == "on" else "⛔ Выключена"
        # bot.send_message(message.chat.id, f"🕒 Текущее расписание:\n{current_schedule}\n ")

        bot.send_message(
            message.chat.id,
            f"🕒 Текущее расписание:\n{current_schedule}\n \n🔄 *Статус автоматической рассылки:* {current_status}\n\n",
            parse_mode="Markdown",
        )

        # Создание inline-кнопок
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="change_time"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_time")
        )

        bot.send_message(message.chat.id, "Желаете изменить время автоматической отправки заданий?",
                         reply_markup=keyboard)

    # ========= Обработка нажатий "Да" / "Нет" =========
    @bot.callback_query_handler(func=lambda call: call.data in ["change_time", "cancel_time"])
    def process_time_change(call):
        """Обрабатывает выбор администратора (изменить время или оставить текущее)."""
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав изменять расписание.")
            return

        if call.data == "change_time":
            # Удаляем inline-кнопки, но оставляем текст сообщения
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

            # Запрашиваем у администратора новое время
            bot.send_message(call.message.chat.id,
                             "⏳ Введите новое время в формате 'HH:MM HH:MM HH:MM' (через пробел):")
            bot.register_next_step_handler(call.message, update_schedule)

        elif call.data == "cancel_time":
            bot.edit_message_text("❌ Изменение отменено.", call.message.chat.id, call.message.message_id)

    # ========= Обновление `work_time` =========
    def update_schedule(message):
        """Обновляет список времени отправки задач в `config.py` и перезапускает планировщик."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять расписание.")
            return

        new_times = message.text.strip().split()

        # Проверяем корректность формата и исправляем, если нужно
        corrected_times = []
        for time_value in new_times:
            match = re.match(r"^(\d{1,2}):(\d{2})$", time_value)
            if not match:
                bot.send_message(
                    message.chat.id,
                    "⚠ Ошибка: введите время в формате 'H:MM' или 'HH:MM'.\n"
                    "Пример: 9:30 или 09:30\n"
                    "Начните сначала, используя команду /set_time."
                )
                return

            hours, minutes = match.groups()
            hours = hours.zfill(2)  # Добавляем ноль перед однозначными числами
            corrected_times.append(f"{hours}:{minutes}")

        # **Перезаписываем `work_time` в config.py**
        config.work_time = corrected_times
        with open("config.py", "r", encoding="utf-8") as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            if line.startswith("work_time"):
                lines[i] = f"work_time = {corrected_times}\n"

        with open("config.py", "w", encoding="utf-8") as file:
            file.writelines(lines)

        # Перезагружаем config.py
        importlib.reload(config)

        current_status = "✅ Включена" if config.status_work_time == "on" else "⛔ Выключена"

        bot.send_message(message.chat.id, f"✅ Время изменено! Новое расписание:\n" + "\n".join(config.work_time))
        bot.send_message(
            message.chat.id,
            f"🔄 *Статус автоматической рассылки:* {current_status}\n\n",
            parse_mode="Markdown",
        )

        # Перезапускаем планировщик
        restart_scheduler()