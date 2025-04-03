import importlib
import config
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from task_storage import assign_task

def handle_cmnd_user_task(bot, is_admin, task_data):
    """Регистрация обработчиков команды /user_task"""
    # ========= Команда /user_task =========
    @bot.message_handler(commands=['user_task'])
    def handle_user_task(message):
        """Запрашивает у администратора текст задачи."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав ставить задачи.")
            return

        bot.send_message(message.chat.id, "✏ Введите текст задачи (или напишите 'отмена' для выхода):")
        bot.register_next_step_handler(message, process_user_task_text)

    def process_user_task_text(message):
        """Обрабатывает введенный текст задачи и предлагает выбрать сотрудников."""
        if message.text.lower() == "отмена":
            bot.send_message(message.chat.id, "🚫 Создание задачи отменено.")
            return

        task_text = message.text.strip()
        chat_id = message.chat.id

        task_data[chat_id] = {"task_text": task_text, "selected_users": []}

        send_employee_selection(message.chat.id)

    def send_employee_selection(chat_id, group_index=0, message_id=None):
        """Постранично отправляет список сотрудников по группам, редактируя сообщение."""
        importlib.reload(config)

        with open("user_cache.json", "r", encoding="utf-8") as f:
            user_cache = json.load(f)

        selected_users = task_data[chat_id]["selected_users"]
        group_names = list(config.performers.keys())

        if group_index < 0:
            group_index = 0
        elif group_index >= len(group_names):
            group_index = len(group_names) - 1

        current_group = group_names[group_index]
        group_users = config.performers[current_group]

        keyboard = InlineKeyboardMarkup()
        available = 0

        for user_id in group_users:
            if user_id in selected_users:
                continue

            cached = user_cache.get(str(user_id), {})
            first_name = cached.get("first_name", "Без имени")
            username = f"@{cached['username']}" if cached.get("username") else f"ID: {user_id}"

            callback_data = f"select_employee|{chat_id}|{user_id}|{group_index}"
            keyboard.add(InlineKeyboardButton(f"{first_name} ({username})", callback_data=callback_data))
            available += 1

        # Навигация
        nav_buttons = []
        if group_index > 0:
            nav_buttons.append(InlineKeyboardButton("⏮ Назад", callback_data=f"prev_group|{chat_id}|{group_index}"))
        if group_index < len(group_names) - 1:
            nav_buttons.append(InlineKeyboardButton("⏭ Вперёд", callback_data=f"next_group|{chat_id}|{group_index}"))
        if nav_buttons:
            keyboard.row(*nav_buttons)

        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_task|{chat_id}"))

        message_text = f"<b>{current_group}</b>\nКому нужно поставить задачу?" if available else f"<b>{current_group}</b>\nНет доступных сотрудников."

        if message_id:
            bot.edit_message_text(
                message_text,
                chat_id,
                message_id,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            bot.send_message(chat_id, message_text, parse_mode="HTML", reply_markup=keyboard)

        task_data[chat_id]["group_index"] = group_index

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("next_group") or call.data.startswith("prev_group"))
    def paginate_groups(call):
        action, chat_id, current_index = call.data.split("|")
        chat_id = int(chat_id)
        current_index = int(current_index)

        new_index = current_index + 1 if action == "next_group" else current_index - 1

        send_employee_selection(chat_id, new_index, message_id=call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_employee"))
    def select_employee(call):
        """Добавляет сотрудника в список получателей задачи."""
        _, chat_id, user_id, group_index = call.data.split("|")
        chat_id, user_id, group_index = int(chat_id), int(user_id), int(group_index)

        if chat_id not in task_data:
            bot.answer_callback_query(call.id, "⚠ Ошибка: задача не найдена.")
            return

        if user_id not in task_data[chat_id]["selected_users"]:
            task_data[chat_id]["selected_users"].append(user_id)

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        send_selected_users(chat_id)

    def send_selected_users(chat_id):
        """Отправляет сообщение с выбранными пользователями и возможностью добавить ещё или отправить."""
        selected_users = task_data[chat_id]["selected_users"]
        with open("user_cache.json", "r", encoding="utf-8") as f:
            user_cache = json.load(f)

        selected_text = ""
        for user_id in selected_users:
            cached = user_cache.get(str(user_id), {})
            first_name = cached.get("first_name", "Без имени")
            username = f"(@{cached['username']})" if cached.get("username") else f"(ID: {user_id})"
            selected_text += f"✅ {first_name} {username} - <code>{user_id}</code>\n"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Добавить ещё", callback_data=f"add_more_users|{chat_id}"),
            InlineKeyboardButton("📨 ОТПРАВИТЬ", callback_data=f"send_task|{chat_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_task|{chat_id}")
        )

        bot.send_message(
            chat_id,
            f"Добавить ещё одного сотрудника или отправить задачу?\n\n<b>Выбранные сотрудники:</b>\n{selected_text}",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("add_more_users"))
    def add_more_users(call):
        """Позволяет выбрать ещё сотрудников."""
        chat_id = int(call.data.split("|")[1])
        group_index = task_data.get(chat_id, {}).get("group_index", 0)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        send_employee_selection(chat_id, group_index)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("send_task"))
    def send_task(call):
        """Отправляет задачу выбранным сотрудникам."""
        chat_id = int(call.data.split("|")[1])

        if chat_id not in task_data or not task_data[chat_id]["selected_users"]:
            bot.answer_callback_query(call.id, "⚠ Ошибка: нет выбранных сотрудников.")
            return

        task_text = task_data[chat_id]["task_text"]
        user_ids = task_data[chat_id]["selected_users"]

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        for user_id in user_ids:
            try:
                msg = bot.send_message(user_id, f"📌 <b>Новое задание:</b>\n{task_text}", parse_mode="HTML")
                assign_task(user_id, task_text, msg.message_id)
                task_data[user_id] = {"task_text": task_text}
            except telebot.apihelper.ApiTelegramException as e:
                print(f"⚠ Ошибка отправки пользователю {user_id}: {e}")

        bot.send_message(chat_id, "✅ Задача успешно отправлена выбранным сотрудникам!")
        del task_data[chat_id]

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_task"))
    def cancel_task(call):
        """Отмена создания задачи."""
        chat_id = int(call.data.split("|")[1])
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(chat_id, "🚫 Создание задачи отменено.")
        if chat_id in task_data:
            del task_data[chat_id]