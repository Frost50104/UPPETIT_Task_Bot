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

def _end_of_month(year, month):
    # Возвращает последний день месяца
    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, month + 1, 1)
    return (next_month - datetime.timedelta(days=1)).day


def _add_months(dt: datetime.datetime, months: int) -> datetime.datetime:
    # Добавляет months к дате, сохраняя время, корректирует день до последнего в месяце
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, _end_of_month(year, month))
    return dt.replace(year=year, month=month, day=day)


def _next_after(now: datetime.datetime, task_dt: datetime.datetime, repeat: str) -> datetime.datetime:
    if repeat == "daily":
        step = datetime.timedelta(days=1)
        while task_dt <= now:
            task_dt += step
        return task_dt
    if repeat == "weekly":
        step = datetime.timedelta(weeks=1)
        while task_dt <= now:
            task_dt += step
        return task_dt
    if repeat == "monthly":
        nd = task_dt
        while nd <= now:
            nd = _add_months(nd, 1)
        return nd
    return task_dt


def send_scheduled_tasks(bot):
    now = datetime.datetime.now().replace(second=0, microsecond=0)
    today = now.strftime("%d.%m")
    current_time = now.strftime("%H:%M")

    tasks = load_planned_tasks()
    remaining_tasks = []

    for task in tasks:
        try:
            task_datetime_str = f"{task['date']} {task['time']}"
            # Парсим без года и приводим к текущему году для корректного сравнения
            task_dt = datetime.datetime.strptime(task_datetime_str, "%d.%m %H:%M").replace(year=now.year)
        except Exception as e:
            # Если формат задачи некорректный — пропускаем её, но оставляем для ручного исправления
            print(f"⚠ Некорректная дата/время в задаче '{task}': {e}")
            remaining_tasks.append(task)
            continue

        repeat = task.get("repeat", "none")

        # ✅ Отправить задачу, если её время пришло или уже прошло (с точностью до минуты)
        if task_dt <= now:
            recipients = []

            # Группы: пытаемся найти по человекочитаемому имени; если не нашли — пробуем по ключам performers_by_group
            if task.get("groups"):
                for group_name in task["groups"]:
                    group_recipients = list(config.performers.get(group_name, []))
                    if not group_recipients:
                        # Фолбэк: иногда в задаче могут оказаться ключи вида 'task_group_X'
                        group_recipients = config.performers_by_group.get(group_name, [])
                    recipients.extend(group_recipients)

            # Индивидуальные пользователи
            if task.get("users"):
                recipients.extend(task["users"])

            # Убираем дубликаты
            unique_recipients = set()
            for uid in recipients:
                try:
                    unique_recipients.add(int(uid))
                except Exception:
                    continue

            for user_id in unique_recipients:
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

            # Переназначаем дату, если задача повторяющаяся, иначе — удаляем
            if repeat in ("daily", "weekly", "monthly"):
                next_dt = _next_after(now, task_dt, repeat)
                task["date"] = next_dt.strftime("%d.%m")
                task["time"] = next_dt.strftime("%H:%M")
                remaining_tasks.append(task)
            # если не повторяется — не добавляем обратно
        else:
            # Сохраняем только будущие задачи
            remaining_tasks.append(task)

    save_planned_tasks(remaining_tasks)