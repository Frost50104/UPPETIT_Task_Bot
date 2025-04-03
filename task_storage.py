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

LOG_FILE = "task_log.txt"

def log_task_action(user_id, message_id, action, user_cache=None, admin_name=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "ВЫПОЛНЕНО" if action == "accept" else "ОТКЛОНЕНО"
    tasks = load_tasks()
    uid_str = str(user_id)
    uid_int = int(user_id)

    # Получаем имя исполнителя
    display_name = uid_str
    if user_cache:
        user_data = user_cache.get(uid_str) or user_cache.get(uid_int)
        if user_data:
            display_name = user_data.get("first_name") or user_data.get("username") or uid_str

    # Ищем текст задачи
    task_text = None

    for uid in [uid_str, uid_int]:
        if str(uid) in tasks:
            for task in tasks[str(uid)]:
                if task["message_id"] == message_id or task.get("reminder_message_id") == message_id:
                    task_text = task["task_text"]
                    break
        if task_text:
            break

    if not task_text:
        # Поиск по всем задачам (если вдруг uid записан в другом формате)
        for task_list in tasks.values():
            for task in task_list:
                if task["message_id"] == message_id or task.get("reminder_message_id") == message_id:
                    task_text = task["task_text"]
                    break
            if task_text:
                break

    if not task_text:
        task_text = "Не найдено"
        print(f"⚠ Не удалось найти текст задачи при логировании для user_id={user_id}, msg_id={message_id}")

    # Админ в скобках
    admin_info = f" (админ: {admin_name})" if admin_name else ""

    log_line = f"[{timestamp}] {display_name} — {status} — {task_text}{admin_info}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)