import json
import os
import tempfile
import threading
from datetime import datetime

TASKS_FILE = "assigned_tasks.json"
_TASKS_LOCK = threading.RLock()


def _atomic_write_json(path: str, data) -> None:
    """Write JSON atomically: write to temp file, fsync, then replace."""
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def load_tasks():
    """Thread-safe loader with JSON corruption handling."""
    with _TASKS_LOCK:
        if not os.path.exists(TASKS_FILE):
            return {}
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted, preserve it for manual inspection and start fresh
            bad_path = TASKS_FILE + ".bad"
            try:
                # If .bad already exists, append timestamp to avoid overwrite
                if os.path.exists(bad_path):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    bad_path = f"{TASKS_FILE}.{ts}.bad"
                os.replace(TASKS_FILE, bad_path)
            except Exception:
                # Best-effort; continue with empty tasks
                pass
            return {}


def save_tasks(tasks) -> None:
    """Thread-safe atomic save."""
    with _TASKS_LOCK:
        _atomic_write_json(TASKS_FILE, tasks)


def assign_task(user_id, task_text, message_id):
    """Add a new task for user in a single locked read-modify-write."""
    with _TASKS_LOCK:
        tasks = load_tasks()  # safe under RLock
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
    with _TASKS_LOCK:
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
    with _TASKS_LOCK:
        tasks = load_tasks()
        for uid in list(tasks.keys()):
            tasks[uid] = [task for task in tasks[uid] if task["status"] != "выполнена"]
            if not tasks[uid]:  # если список задач пуст — удалить пользователя из словаря
                del tasks[uid]
        save_tasks(tasks)


def clear_all_tasks():
    with _TASKS_LOCK:
        save_tasks({})


def set_reminder_message_id(user_id, original_message_id, reminder_message_id):
    with _TASKS_LOCK:
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
        try:
            if callable(user_cache):
                user_data = user_cache(user_id)
            else:
                user_data = user_cache.get(uid_str) or user_cache.get(uid_int)
            if user_data:
                display_name = user_data.get("first_name") or user_data.get("username") or uid_str
        except Exception as e:
            print(f"⚠ Ошибка при получении данных пользователя из кэша: {e}")

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