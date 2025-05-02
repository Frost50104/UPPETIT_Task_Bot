import config
from bot_instance import task_data
from task_storage import assign_task

# ========= Автоматическая отправка задач по расписанию =========
def send_control_panel_tasks(bot):
    # Словарь для отслеживания отправленных задач пользователям
    sent_tasks = {}

    for group_name, performers in config.performers_by_group.items():
        tasks_text = config.daily_tasks.get(group_name)
        if not tasks_text:
            continue
        for performer in performers:
            # Проверяем, получал ли пользователь уже эту задачу
            if performer in sent_tasks and sent_tasks[performer] == tasks_text:
                continue

            try:
                msg = bot.send_message(performer, f"📌 <b>Задача на сегодня:</b>\n{tasks_text}", parse_mode="HTML")
                assign_task(performer, tasks_text, msg.message_id)
                task_data[performer] = {"task_text": tasks_text}
                # Отмечаем, что пользователь получил эту задачу
                sent_tasks[performer] = tasks_text
            except Exception as e:
                print(f"⚠ Ошибка: {e}")
