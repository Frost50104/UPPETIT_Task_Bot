
import hashlib
import importlib
import config
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

group_name_map = {}

def handle_cmnd_group_task(bot, is_admin, task_data):
    """Регистрация обработчиков команды /group_task"""

    # ========= Команда /group_task =========
    @bot.message_handler(commands=['group_task'])
    def handle_group_task(message):
        """Запрашивает у администратора текст задачи."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав ставить задачи.")
            return

        bot.send_message(message.chat.id, "✏ Введите текст задачи (или напишите 'отмена' для выхода):")
        bot.register_next_step_handler(message, process_group_task_text)

    def process_group_task_text(message):
        """Обрабатывает введенный текст задачи и предлагает выбрать группы сотрудников."""
        if message.text.lower() == "отмена":
            bot.send_message(message.chat.id, "🚫 Создание задачи отменено.")
            return

        task_text = message.text.strip()
        chat_id = message.chat.id

        # Сохраняем данные о задаче
        task_data[chat_id] = {"task_text": task_text, "selected_groups": []}

        send_group_selection(chat_id)

    def hash_group_name(group_name):
        """Создаёт короткий хеш названия группы для использования в callback_data."""
        return hashlib.md5(group_name.encode()).hexdigest()[:8]  # 8 символов достаточно для уникальности

    group_name_map = {}  # Словарь для хранения соответствия хеша и оригинального названия

    def send_group_selection(chat_id):
        """Отправляет список групп для выбора."""
        importlib.reload(config)  # Обновляем данные

        selected_groups = task_data[chat_id]["selected_groups"]
        available_groups = [group for group in config.performers.keys() if group not in selected_groups]

        keyboard = InlineKeyboardMarkup()

        if not available_groups:
            bot.send_message(
                chat_id,
                "Больше нет доступных групп",
                parse_mode="HTML"
            )
            send_selected_groups(chat_id)
            return

        for group_name in available_groups:
            group_hash = hash_group_name(group_name)
            group_name_map[group_hash] = group_name  # Сохраняем соответствие
            callback_data = f"group_task_select|{chat_id}|{group_hash}"
            keyboard.add(InlineKeyboardButton(group_name, callback_data=callback_data))

        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data=f"group_task_cancel|{chat_id}"))

        bot.send_message(
            chat_id,
            "Кому нужно поставить задачу?",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("group_task_select"))
    def select_group(call):
        """Добавляет группу в список получателей задачи и предлагает выбрать еще или отправить."""
        _, chat_id, group_hash = call.data.split("|")
        chat_id = int(chat_id)

        if chat_id not in task_data:
            bot.answer_callback_query(call.id, "⚠ Ошибка: задача не найдена.")
            return

        group_name = group_name_map.get(group_hash)
        if not group_name:
            bot.answer_callback_query(call.id, "⚠ Ошибка: группа не найдена.")
            return

        if group_name not in task_data[chat_id]["selected_groups"]:
            task_data[chat_id]["selected_groups"].append(group_name)

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        send_selected_groups(chat_id)

    def send_selected_groups(chat_id):
        """Отправляет сообщение с выбранными группами и возможностью добавить ещё или отправить."""
        selected_groups = task_data[chat_id]["selected_groups"]
        selected_text = "\n".join([f"✅ <b>{group}</b>" for group in selected_groups])

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Добавить ещё", callback_data=f"group_task_add_more|{chat_id}"),
            InlineKeyboardButton("📨 ОТПРАВИТЬ", callback_data=f"group_task_send|{chat_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"group_task_cancel|{chat_id}")
        )

        bot.send_message(
            chat_id,
            f"Добавить ещё одну группу или отправить задачу?\n\n<b>Выбранные группы:</b>\n{selected_text}",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("group_task_add_more"))
    def add_more_groups(call):
        """Позволяет выбрать ещё группы."""
        chat_id = int(call.data.split("|")[1])
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        send_group_selection(chat_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("group_task_send"))
    def send_group_task(call):
        """Отправляет задачу выбранным группам."""
        chat_id = int(call.data.split("|")[1])

        if chat_id not in task_data or not task_data[chat_id]["selected_groups"]:
            bot.answer_callback_query(call.id, "⚠ Ошибка: нет выбранных групп.")
            return

        task_text = task_data[chat_id]["task_text"]
        group_names = task_data[chat_id]["selected_groups"]
        user_ids = []

        for group_name in group_names:
            user_ids.extend(config.performers.get(group_name, []))

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        for user_id in user_ids:
            try:
                bot.send_message(user_id, f"📌 <b>Новое задание:</b>\n{task_text}", parse_mode="HTML")
                bot.send_message(user_id, "📷 Отправьте фото выполнения.")
                task_data[user_id] = {"task_text": task_text}
            except telebot.apihelper.ApiTelegramException as e:
                print(f"⚠ Ошибка отправки пользователю {user_id}: {e}")

        bot.send_message(chat_id, "✅ Задача успешно отправлена сотрудникам из выбранных групп!")
        del task_data[chat_id]

    @bot.callback_query_handler(func=lambda call: call.data.startswith("group_task_cancel"))
    def cancel_task(call):
        """Отмена создания задачи."""
        chat_id = int(call.data.split("|")[1])
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(chat_id, "🚫 Создание задачи отменено.")
        if chat_id in task_data:
            del task_data[chat_id]