import config
from bot_instance import task_data

# ========= Автоматическая отправка задач по расписанию =========
def send_control_panel_tasks(bot):
    for group_name, performers in config.performers_by_group.items():
        tasks_text = config.daily_tasks.get(group_name)
        if not tasks_text:
            continue
        for performer in performers:
            try:
                bot.send_message(performer, f"📌 <b>Задача на сегодня:</b>\n{tasks_text}", parse_mode="HTML")
                bot.send_message(performer, "📷 Отправьте фото выполнения.")
                task_data[performer] = {"task_text": tasks_text}
            except Exception as e:
                print(f"⚠ Ошибка: {e}")