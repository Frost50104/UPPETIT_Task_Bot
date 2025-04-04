import json
import datetime
import config
from task_storage import assign_task

planned_tasks_file = "planned_tasks.json"
sent_log_file = "sent_log.json"

def load_planned_tasks():
    try:
        with open(planned_tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_planned_tasks(data):
    with open(planned_tasks_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def log_sent_task(user_id, task_text, date_str, time_str):
    try:
        with open(sent_log_file, "r", encoding="utf-8") as f:
            log = json.load(f)
    except FileNotFoundError:
        log = []

    log_entry = {
        "user_id": user_id,
        "text": task_text,
        "sent_at": f"{date_str} {time_str}"
    }
    log.append(log_entry)

    with open(sent_log_file, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=4)

def send_scheduled_tasks(bot):
    now = datetime.datetime.now()
    today = now.strftime("%d.%m")
    current_time = now.strftime("%H:%M")

    tasks = load_planned_tasks()
    remaining_tasks = []

    for task in tasks:
        task_datetime_str = f"{task['date']} {task['time']}"
        task_datetime = datetime.datetime.strptime(task_datetime_str, "%d.%m %H:%M")

        # ✅ Отправить задачу, если дата и время пришли
        if task_datetime.strftime("%d.%m %H:%M") == now.strftime("%d.%m %H:%M"):
            recipients = []

            if task.get("groups"):
                for group_name in task["groups"]:
                    recipients.extend(config.performers.get(group_name, []))

            if task.get("users"):
                recipients.extend(task["users"])

            for user_id in set(recipients):
                try:
                    msg = bot.send_message(
                        user_id,
                        f"📌 <b>Запланированная задача:</b>\n{task['text']}",
                        parse_mode="HTML"
                    )
                    assign_task(user_id, task["text"], msg.message_id)
                    log_sent_task(user_id, task["text"], today, current_time)
                except Exception as e:
                    print(f"⚠ Ошибка при отправке пользователю {user_id}: {e}")

            # Задача считается выполненной и не попадает в оставшиеся
        else:
            # Сохраняем только будущие задачи
            remaining_tasks.append(task)

    save_planned_tasks(remaining_tasks)