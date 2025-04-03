import json
import os
from datetime import datetime

TASKS_FILE = "assigned_tasks.json"

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def assign_task(user_id, task_text, message_id):
    tasks = load_tasks()
    uid = str(user_id)
    if uid not in tasks:
        tasks[uid] = []
    tasks[uid].append({
        "task_text": task_text,
        "status": "не выполнена",
        "message_id": message_id,
        "assigned_at": datetime.now().isoformat(),
        "control_msg_id": None
    })
    save_tasks(tasks)

def update_task_status(user_id, message_id, status, control_msg_id=None):
    tasks = load_tasks()
    uid = str(user_id)
    if uid in tasks:
        for task in tasks[uid]:
            if task["message_id"] == message_id or task.get("reminder_message_id") == message_id:
                task["status"] = status
                if control_msg_id is not None:
                    task["control_msg_id"] = control_msg_id
                if status == "выполнена" and "reminder_message_id" in task:
                    del task["reminder_message_id"]
                break
        save_tasks(tasks)

def clear_completed_tasks():
    tasks = load_tasks()
    for uid in list(tasks.keys()):
        tasks[uid] = [task for task in tasks[uid] if task["status"] != "выполнена"]
        if not tasks[uid]:  # если список задач пуст — удалить пользователя из словаря
            del tasks[uid]
    save_tasks(tasks)

def clear_all_tasks():
    save_tasks({})

def set_reminder_message_id(user_id, original_message_id, reminder_message_id):
    tasks = load_tasks()
    uid = str(user_id)
    if uid in tasks:
        for task in tasks[uid]:
            if task["message_id"] == original_message_id:
                task["reminder_message_id"] = reminder_message_id
                save_tasks(tasks)
                return