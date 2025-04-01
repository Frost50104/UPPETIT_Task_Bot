import re
import importlib
import config
from bot_instance import task_data
import restart_scheduler
from telebot.types import Message


def handle_cmnd_set_month(bot, is_admin, restart_scheduler):
    """Регистрация обработчиков команды /set_month"""

    @bot.message_handler(commands=['set_month'])
    def handle_set_month(message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять расписание.")
            return

        current_schedule = "\n".join([f"{day}-го числа в {time}" for day, time in config.monthly_schedule])
        current_status = "✅ Включена" if config.status_monthly == "on" else "⛔ Выключена"

        bot.send_message(
            message.chat.id,
            f"📅 <b>Текущее ежемесячное расписание:</b>\n{current_schedule}\n\n"
            f"🔄 <b>Статус:</b> {current_status}\n\n"
            f"Введите новое расписание в формате <i>число время</i>, например:\n"
            f"<code>1 10:00 15 18:30</code>",
            parse_mode="HTML"
        )

        bot.register_next_step_handler(message, update_monthly_schedule)

    def update_monthly_schedule(message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Нет доступа.")
            return

        parts = message.text.strip().split()
        if len(parts) % 2 != 0:
            bot.send_message(message.chat.id, "⚠ Неверный формат. Введите пары: число и время.")
            return

        new_schedule = []
        for i in range(0, len(parts), 2):
            try:
                day = int(parts[i])
                time_part = parts[i + 1]
            except ValueError:
                bot.send_message(message.chat.id, f"⚠ Неверное число: {parts[i]}")
                return

            if not (1 <= day <= 31):
                bot.send_message(message.chat.id, f"⚠ День должен быть от 1 до 31: {day}")
                return

            if not re.match(r"^\d{1,2}:\d{2}$", time_part):
                bot.send_message(message.chat.id, f"⚠ Неверный формат времени: {time_part}")
                return

            time_part = time_part.zfill(5)
            new_schedule.append((day, time_part))

        with open("config.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith("monthly_schedule"):
                lines[i] = f"monthly_schedule = {new_schedule}\n"

        with open("config.py", "w", encoding="utf-8") as f:
            f.writelines(lines)

        importlib.reload(config)
        bot.send_message(message.chat.id, "✅ Ежемесячное расписание обновлено!")
        restart_scheduler()

    def send_monthly_tasks():
        for group_name, performers in config.performers_by_group.items():
            tasks_text = config.monthly_tasks.get(group_name)
            if not tasks_text:
                continue
            for performer in performers:
                try:
                    bot.send_message(performer, f"📌 <b>Ежемесячная задача:</b>\n{tasks_text}", parse_mode="HTML")
                    bot.send_message(performer, "📷 Отправьте фото выполнения.")
                    task_data[performer] = {"task_text": tasks_text}
                except Exception as e:
                    print(f"⚠ Ошибка: {e}")
