
import re
import importlib
import config
from telebot.types import Message
from bot_instance import task_data

import schedule

def handle_cmnd_set_day(bot, is_admin, restart_scheduler):
    """Регистрация обработчиков команды /set_day"""

    @bot.message_handler(commands=['set_day'])
    def handle_set_day(message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять недельное расписание.")
            return

        # Перевод с английского на русский
        day_translate_reverse = {
            "monday": "Понедельник",
            "tuesday": "Вторник",
            "wednesday": "Среда",
            "thursday": "Четверг",
            "friday": "Пятница",
            "saturday": "Суббота",
            "sunday": "Воскресенье"
        }

        current_schedule = "\n".join([
            f"{day_translate_reverse.get(day, day)} в {time}"
            for day, time in config.weekly_schedule
        ])
        current_status = "✅ Включена" if config.status_weekly == "on" else "⛔ Выключена"

        bot.send_message(
            message.chat.id,
            f"📅 <b>Текущее недельное расписание:</b>\n{current_schedule}\n\n"
            f"🔄 <b>Статус:</b> {current_status}\n\n"
            f"Введите новое расписание в формате <i>день время</i>, например:\n"
            f"<code>понедельник 10:00 среда 15:30</code>",
            parse_mode="HTML"
        )

        bot.register_next_step_handler(message, update_weekly_schedule)

    def update_weekly_schedule(message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Нет доступа.")
            return

        parts = message.text.strip().split()
        if len(parts) % 2 != 0:
            bot.send_message(message.chat.id,
                             "⚠ Неверный формат. Используйте команду /set_day еще раз и введите корректно пары: день и время.")
            return

        # Словарь соответствия русских и английских дней
        day_translation = {
            "понедельник": "monday",
            "вторник": "tuesday",
            "среда": "wednesday",
            "четверг": "thursday",
            "пятница": "friday",
            "суббота": "saturday",
            "воскресенье": "sunday"
        }

        new_schedule = []
        for i in range(0, len(parts), 2):
            day_input = parts[i].lower()
            time_part = parts[i + 1]

            # Преобразуем день недели
            day = day_translation.get(day_input, day_input)
            if day not in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                bot.send_message(message.chat.id, f"⚠ Неверный день недели: {day_input}")
                return

            if not re.match(r"^\d{1,2}:\d{2}$", time_part):
                bot.send_message(message.chat.id, f"⚠ Неверный формат времени: {time_part}")
                return

            time_part = time_part.zfill(5)  # Приводим к формату HH:MM
            new_schedule.append((day, time_part))

        # Обновляем config.py
        with open("config.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith("weekly_schedule"):
                lines[i] = f"weekly_schedule = {new_schedule}\n"

        with open("config.py", "w", encoding="utf-8") as f:
            f.writelines(lines)

        importlib.reload(config)
        bot.send_message(message.chat.id, "✅ Недельное расписание обновлено!")
        restart_scheduler()

    def send_weekly_tasks():
        for group_name, performers in config.performers_by_group.items():
            tasks_text = config.weekly_tasks.get(group_name)
            if not tasks_text:
                continue
            for performer in performers:
                try:
                    bot.send_message(performer, f"📌 <b>Еженедельная задача:</b>\n{tasks_text}", parse_mode="HTML")
                    bot.send_message(performer, "📷 Отправьте фото выполнения.")
                    task_data[performer] = {"task_text": tasks_text}
                except Exception as e:
                    print(f"⚠ Ошибка: {e}")

    # Еженедельная рассылка
    if config.status_weekly == "on":
        for day, time_str in config.weekly_schedule:
            getattr(schedule.every(), day).at(time_str).do(send_weekly_tasks)