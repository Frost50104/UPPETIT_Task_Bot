import importlib
import config
import json
import hashlib
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.date_utils import parse_datetime_string
from task_storage import assign_task

planned_tasks_file = "planned_tasks.json"
group_name_map = {}
user_cache = {}

# Загрузка запланированных задач
def load_planned_tasks():
    try:
        with open(planned_tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Сохранение задач
def save_planned_tasks(data):
    with open(planned_tasks_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Генерация короткого хеша
def hash_name(name):
    return hashlib.md5(name.encode()).hexdigest()[:10]

def handle_cmnd_planning(bot, is_admin, task_data):
    @bot.message_handler(commands=["planning"])
    def handle_planning_command(message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет доступа.")
            return
        show_tasks(message.chat.id)

    def show_tasks(chat_id):
        tasks = load_planned_tasks()
        if not tasks:
            text = "📋 Сейчас нет запланированных задач."
        else:
            lines = ["📋 <b>Запланированные задачи:</b>"]

            # Подгружаем user_cache
            global user_cache
            if not user_cache:
                try:
                    with open("user_cache.json", "r", encoding="utf-8") as f:
                        user_cache = json.load(f)
                except FileNotFoundError:
                    user_cache = {}

            for i, task in enumerate(tasks, 1):
                recipients = []

                if task.get("groups"):
                    recipients += task["groups"]

                if task.get("users"):
                    for uid in task["users"]:
                        cached = user_cache.get(str(uid), {})
                        name = cached.get("first_name") or f"ID:{uid}"
                        recipients.append(name)

                repeat = task.get('repeat', 'none')
                rep_label = {
                    'none': 'Однократно',
                    'daily': 'Ежедневно',
                    'weekly': 'Еженедельно',
                    'monthly': 'Ежемесячно'
                }.get(repeat, 'Однократно')
                lines.append(
                    f"<b>{i}. {task['text']}</b>\n🕒 {task['date']} {task['time']} • 🔁 {rep_label}\n👥 {', '.join(recipients)}"
                )
            text = "\n\n".join(lines)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Добавить", callback_data="planning_add"),
            InlineKeyboardButton("📝 Редактировать", callback_data="planning_edit"),
            InlineKeyboardButton("❌ Удалить задачу", callback_data="planning_delete")
        )
        keyboard.add(InlineKeyboardButton("🔙 Отмена", callback_data="planning_cancel"))
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == "planning_cancel")
    def cancel_planning_main(call):
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "🚫 Действие отменено.")

    # === ДОБАВЛЕНИЕ ===
    @bot.callback_query_handler(func=lambda call: call.data == "planning_add")
    def planning_add_task(call):
        cid = call.message.chat.id
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        bot.send_message(cid, "✏ Введите текст задачи:")
        task_data[cid] = {"state": "adding_text"}

    @bot.message_handler(func=lambda m: task_data.get(m.chat.id, {}).get("state") == "adding_text")
    def input_text(message):
        cid = message.chat.id
        task_data[cid]["text"] = message.text.strip()
        task_data[cid]["state"] = "adding_datetime"
        bot.send_message(cid, "📅 Введите дату и время (дд.мм чч:мм):")

    @bot.message_handler(func=lambda m: task_data.get(m.chat.id, {}).get("state") == "adding_datetime")
    def input_datetime(message):
        cid = message.chat.id
        parsed = parse_datetime_string(message.text.strip())
        if not parsed:
            bot.send_message(cid, "⚠ Неверный формат. Повторите ввод: дд.мм чч:мм")
            return
        task_data[cid]["date"], task_data[cid]["time"] = parsed
        # По умолчанию — без повторения
        task_data[cid]["repeat"] = task_data[cid].get("repeat", "none")
        task_data[cid]["state"] = "choosing_repeat"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("❌ Однократно", callback_data="set_repeat|none"),
            InlineKeyboardButton("🔁 Ежедневно", callback_data="set_repeat|daily")
        )
        keyboard.add(
            InlineKeyboardButton("📅 Еженедельно", callback_data="set_repeat|weekly"),
            InlineKeyboardButton("📆 Ежемесячно", callback_data="set_repeat|monthly")
        )
        keyboard.add(InlineKeyboardButton("🔙 Отмена", callback_data="cancel_planning_task"))
        bot.send_message(cid, "Выберите режим повторения:", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("set_repeat|"))
    def set_repeat(call):
        cid = call.message.chat.id
        _, value = call.data.split("|")
        if value not in ["none", "daily", "weekly", "monthly"]:
            value = "none"
        prev_state = task_data.get(cid, {}).get("state")
        task_data.setdefault(cid, {})
        task_data[cid]["repeat"] = value

        # Убираем инлайн-кнопки выбора режима повторения из сообщения
        try:
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception:
            pass

        # Если редактируем только повторение — сохранение сразу
        if prev_state == "editing_repeat" and "edit_index" in task_data[cid]:
            tasks = load_planned_tasks()
            index = task_data[cid]["edit_index"]
            if 0 <= index < len(tasks):
                tasks[index]["repeat"] = value
                save_planned_tasks(tasks)
            task_data.pop(cid, None)
            bot.send_message(cid, "✅ Режим повторения обновлён.")
            show_tasks(cid)
            return

        # Иначе продолжаем создание и выбираем получателей
        task_data[cid]["state"] = "choosing_type"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("👥 Группам", callback_data="planning_to_groups"),
            InlineKeyboardButton("👤 Сотрудникам", callback_data="planning_to_users")
        )
        bot.send_message(cid, "Кому отправить задачу?", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data in ["planning_to_groups", "planning_to_users"])
    def choose_recipients(call):
        cid = call.message.chat.id
        task_data[cid]["recipients"] = []
        task_data[cid]["recipient_type"] = "groups" if "groups" in call.data else "users"
        task_data[cid]["user_page"] = 0
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        send_recipient_options(cid)

    def send_recipient_options(cid):
        importlib.reload(config)
        rtype = task_data[cid]["recipient_type"]
        selected = task_data[cid]["recipients"]

        page = task_data[cid].get("user_page", 0)
        per_page = 10

        keyboard = InlineKeyboardMarkup()
        if rtype == "groups":
            for name in config.performers:
                if name not in selected:
                    h = hash_name(name)
                    group_name_map[h] = name
                    keyboard.add(InlineKeyboardButton(name, callback_data=f"select_recipient|{h}"))
        else:
            global user_cache
            if not user_cache:
                with open("user_cache.json", "r", encoding="utf-8") as f:
                    user_cache = json.load(f)

            uids = [int(uid) for uid in user_cache if int(uid) not in selected]
            uids.sort()

            start = page * per_page
            end = start + per_page
            paged_uids = uids[start:end]

            for uid in paged_uids:
                user = user_cache[str(uid)]
                label = f"{user.get('first_name', 'Без имени')} (@{user.get('username') or uid})"
                keyboard.add(InlineKeyboardButton(label, callback_data=f"select_recipient|{uid}"))

            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⏮ Назад", callback_data="user_page_prev"))
            if end < len(uids):
                nav_buttons.append(InlineKeyboardButton("⏭ Вперёд", callback_data="user_page_next"))
            if nav_buttons:
                keyboard.row(*nav_buttons)

        keyboard.add(
            InlineKeyboardButton("✅ Сохранить задачу", callback_data="save_task"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel_planning_task")
        )

        if rtype == "groups":
            selected_display = "\n".join([f"✅ {v}" for v in selected]) or "–"
        else:
            selected_display = ""
            for uid in selected:
                cached = user_cache.get(str(uid), {})
                name = cached.get("first_name") or str(uid)
                selected_display += f"✅ {name}\n"

        label = "группы" if rtype == "groups" else "сотрудники"
        bot.send_message(cid, f"Выбранные {label}:\n{selected_display or '–'}", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == "user_page_prev")
    def user_page_prev(call):
        cid = call.message.chat.id
        task_data[cid]["user_page"] = max(task_data[cid].get("user_page", 0) - 1, 0)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        send_recipient_options(cid)

    @bot.callback_query_handler(func=lambda call: call.data == "user_page_next")
    def user_page_next(call):
        cid = call.message.chat.id
        task_data[cid]["user_page"] = task_data[cid].get("user_page", 0) + 1
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        send_recipient_options(cid)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_recipient|"))
    def select_recipient(call):
        cid = call.message.chat.id
        _, value = call.data.split("|")
        rtype = task_data[cid]["recipient_type"]

        if rtype == "groups":
            name = group_name_map.get(value)
            if name and name not in task_data[cid]["recipients"]:
                task_data[cid]["recipients"].append(name)
        else:
            uid = int(value)
            if uid not in task_data[cid]["recipients"]:
                task_data[cid]["recipients"].append(uid)

        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        send_recipient_options(cid)

    @bot.callback_query_handler(func=lambda call: call.data == "save_task")
    def save_task(call):
        cid = call.message.chat.id
        d = task_data.get(cid, {})
        is_editing = "edit_index" in d

        if not d.get("recipients"):
            bot.send_message(cid, "⚠ Вы не выбрали получателей.")
            return

        if is_editing:
            tasks = load_planned_tasks()
            index = d["edit_index"]
            task = tasks[index]

            # Обновляем
            if d["recipient_type"] == "groups":
                task["groups"] = d["recipients"]
                task["users"] = []
            else:
                task["users"] = d["recipients"]
                task["groups"] = []

            task["text"] = d.get("text", task["text"])
            task["date"] = d.get("date", task["date"])
            task["time"] = d.get("time", task["time"])
            task["repeat"] = d.get("repeat", task.get("repeat", "none"))

            tasks[index] = task
            save_planned_tasks(tasks)
            task_data.pop(cid, None)

            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
            bot.send_message(cid, "✅ Задача обновлена.")
            show_tasks(cid)
            return  # ☝️ ОЧЕНЬ ВАЖНО: не продолжаем

        # ⬇️ Этот блок выполнится только при создании новой задачи
        task = {
            "text": d["text"],
            "date": d["date"],
            "time": d["time"],
            "repeat": d.get("repeat", "none"),
            "groups": d["recipients"] if d["recipient_type"] == "groups" else [],
            "users": d["recipients"] if d["recipient_type"] == "users" else []
        }

        tasks = load_planned_tasks()
        tasks.append(task)
        save_planned_tasks(tasks)

        task_data.pop(cid, None)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        bot.send_message(cid, "✅ Задача добавлена в план.")
        show_tasks(cid)

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_planning_task")
    def cancel_planning_task(call):
        cid = call.message.chat.id
        state = task_data.get(cid, {}).get("state")

        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)

        if state in ["adding_text", "adding_datetime", "choosing_type",
                     "editing", "editing_text", "editing_datetime"]:
            task_data.pop(cid, None)
            bot.send_message(cid, "🚫 Действие отменено.")
            show_tasks(cid)
        else:
            bot.send_message(cid, "🚫 Действие отменено.")
            task_data.pop(cid, None)

    # === УДАЛЕНИЕ ===
    @bot.callback_query_handler(func=lambda call: call.data == "planning_delete")
    def choose_task_to_delete(call):
        cid = call.message.chat.id
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        tasks = load_planned_tasks()
        if not tasks:
            bot.send_message(cid, "⚠ Нет задач для удаления.")
            return
        keyboard = InlineKeyboardMarkup()
        for i, task in enumerate(tasks):
            label = task["text"][:15] + "..." if len(task["text"]) > 15 else task["text"]
            keyboard.add(InlineKeyboardButton(label, callback_data=f"delete_task|{i}"))
        bot.send_message(cid, "Выберите задачу для удаления:", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_task|"))
    def delete_task(call):
        cid = call.message.chat.id
        index = int(call.data.split("|")[1])
        tasks = load_planned_tasks()
        if index >= len(tasks):
            bot.send_message(cid, "⚠ Задача не найдена.")
            return
        del tasks[index]
        save_planned_tasks(tasks)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        bot.send_message(cid, "🗑 Задача удалена.")
        show_tasks(cid)

    # === РЕДАКТИРОВАНИЕ ===
    @bot.callback_query_handler(func=lambda call: call.data == "planning_edit")
    def choose_task_to_edit(call):
        cid = call.message.chat.id
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        tasks = load_planned_tasks()
        if not tasks:
            bot.send_message(cid, "⚠ Нет задач для редактирования.")
            return
        keyboard = InlineKeyboardMarkup()
        for i, task in enumerate(tasks):
            label = (task["text"][:22] + "...") if len(task["text"]) > 25 else task["text"]
            keyboard.add(InlineKeyboardButton(label, callback_data=f"planning_edit_task|{i}"))
        bot.send_message(cid, "Выберите задачу для редактирования:", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("planning_edit_task|"))
    def edit_task_options(call):
        cid = call.message.chat.id
        index = int(call.data.split("|")[1])
        tasks = load_planned_tasks()
        if index >= len(tasks):
            bot.send_message(cid, "⚠ Задача не найдена.")
            return

        task_data[cid] = {"edit_index": index, "state": "editing"}

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✏ Текст", callback_data="edit_field|text"),
            InlineKeyboardButton("📅 Дата и время", callback_data="edit_field|datetime"),
            InlineKeyboardButton("🔁 Повторение", callback_data="edit_field|repeat"),
            InlineKeyboardButton("👥 Получатели", callback_data="edit_field|recipients")
        )
        keyboard.add(InlineKeyboardButton("🔙 Отмена", callback_data="cancel_planning_task"))

        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        bot.send_message(cid, "Что нужно изменить?", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_field|"))
    def handle_edit_field(call):
        cid = call.message.chat.id
        field = call.data.split("|")[1]

        task_data[cid]["edit_field"] = field

        if field == "text":
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
            bot.send_message(cid, "✏ Введите новый текст задачи:")
            task_data[cid]["state"] = "editing_text"
        elif field == "datetime":
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
            bot.send_message(cid, "📅 Введите новую дату и время (дд.мм чч:мм):")
            task_data[cid]["state"] = "editing_datetime"
        elif field == "recipients":
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)

            # Загружаем задачу в task_data (если еще не загружена)
            tasks = load_planned_tasks()
            index = task_data[cid]["edit_index"]
            task = tasks[index]

            task_data[cid]["text"] = task["text"]
            task_data[cid]["date"] = task["date"]
            task_data[cid]["time"] = task["time"]
            task_data[cid]["repeat"] = task.get("repeat", "none")
            task_data[cid]["state"] = "choosing_type"

            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("👥 Группам", callback_data="planning_to_groups"),
                InlineKeyboardButton("👤 Сотрудникам", callback_data="planning_to_users")
            )
            bot.send_message(cid, "Кому отправить задачу?", reply_markup=keyboard)
        elif field == "repeat":
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
            task_data[cid]["state"] = "editing_repeat"

            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("❌ Однократно", callback_data="set_repeat|none"),
                InlineKeyboardButton("🔁 Ежедневно", callback_data="set_repeat|daily")
            )
            keyboard.add(
                InlineKeyboardButton("📅 Еженедельно", callback_data="set_repeat|weekly"),
                InlineKeyboardButton("📆 Ежемесячно", callback_data="set_repeat|monthly")
            )
            keyboard.add(InlineKeyboardButton("🔙 Отмена", callback_data="cancel_planning_task"))
            bot.send_message(cid, "Выберите режим повторения:", reply_markup=keyboard)

    @bot.message_handler(func=lambda m: task_data.get(m.chat.id, {}).get("state") == "editing_text")
    def save_new_text(message):
        cid = message.chat.id
        new_text = message.text.strip()
        tasks = load_planned_tasks()
        index = task_data[cid]["edit_index"]
        tasks[index]["text"] = new_text
        save_planned_tasks(tasks)
        task_data.pop(cid, None)
        bot.send_message(cid, "✅ Текст задачи обновлён.")
        show_tasks(cid)

    @bot.message_handler(func=lambda m: task_data.get(m.chat.id, {}).get("state") == "editing_datetime")
    def save_new_datetime(message):
        cid = message.chat.id
        parsed = parse_datetime_string(message.text.strip())
        if not parsed:
            bot.send_message(cid, "⚠ Неверный формат. Повторите ввод: дд.мм чч:мм")
            return

        tasks = load_planned_tasks()
        index = task_data[cid]["edit_index"]
        tasks[index]["date"], tasks[index]["time"] = parsed
        save_planned_tasks(tasks)
        task_data.pop(cid, None)
        bot.send_message(cid, "✅ Дата и время обновлены.")
        show_tasks(cid)