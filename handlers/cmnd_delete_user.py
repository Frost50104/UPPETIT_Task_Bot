# Обработчик комнады /delete_user
import importlib
import config
import re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def handle_cmnd_delete_user(bot, is_admin, task_data):
    """Регистрация обработчиков команды /delete_user"""
    # ========= Команда /delete_user =========
    @bot.message_handler(commands=['delete_user'])
    def handle_delete_user(message):
        """Запускает процесс удаления сотрудника."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав удалять сотрудников.")
            return

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="confirm_delete_user"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_delete_user")
        )

        bot.send_message(
            message.chat.id,
            "Хотите удалить пользователя?",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data in ["confirm_delete_user", "cancel_delete_user"])
    def process_delete_user_choice(call):
        """Обрабатывает выбор администратора."""
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав удалять сотрудников.")
            return

        if call.data == "cancel_delete_user":
            bot.edit_message_text("❌ Удаление сотрудника отменено.", call.message.chat.id, call.message.message_id)
            return

        # Перезагружаем config перед выводом списка групп
        importlib.reload(config)

        # Используем индекс вместо длинного названия группы
        group_index_map = {str(index): name for index, name in enumerate(config.performers.keys())}

        # Сохраняем соответствие индексов и имен групп (глобально)
        task_data[call.message.chat.id] = {"group_index_map": group_index_map}

        keyboard = InlineKeyboardMarkup()
        for index, group_name in group_index_map.items():
            keyboard.add(InlineKeyboardButton(group_name[:30], callback_data=f"delete_group_{index}"))

        # Добавляем кнопку "❌ Отмена"
        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete_employee_group"))

        bot.edit_message_text(
            "Выберите группу, из которой нужно удалить сотрудника:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_delete_employee_group")
    def cancel_delete_employee(call):
        """Отменяет удаление сотрудника и завершает процесс."""
        bot.edit_message_text("🚫 Удаление сотрудника отменено.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_group_"))
    def select_group_to_delete(call):
        """Обрабатывает выбор группы для удаления сотрудника."""
        chat_id = call.message.chat.id
        group_index = call.data.split("_")[2]

        if chat_id not in task_data or "group_index_map" not in task_data[chat_id]:
            bot.send_message(chat_id, "⚠ Ошибка: данные не найдены. Повторите команду /delete_user.")
            return

        # Получаем название группы по индексу
        group_name = task_data[chat_id]["group_index_map"].get(group_index)

        if not group_name:
            bot.send_message(chat_id, "⚠ Ошибка: группа не найдена.")
            return

        # Сохраняем выбранную группу
        task_data[chat_id]["selected_group"] = group_name

        # Получаем список сотрудников
        employee_list = config.performers[group_name]
        if not employee_list:
            bot.send_message(chat_id, f"⚠ В группе <b>{group_name}</b> нет сотрудников.", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup()
        for user_id in employee_list:
            try:
                user = bot.get_chat(user_id)
                username = f"@{user.username}" if user.username else "Без username"
                first_name = user.first_name or "Без имени"
                display_text = f"👤 {first_name} ({username})"
            except telebot.apihelper.ApiTelegramException:
                display_text = f"❌ ID: {user_id} (не найден)"

            keyboard.add(InlineKeyboardButton(display_text, callback_data=f"delete_user_{user_id}"))

        # Добавляем кнопку "❌ Отмена"
        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete_employee"))

        bot.edit_message_text(
            f"Выберите сотрудника для удаления из <b>{group_name}</b>:",
            chat_id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_delete_employee")
    def cancel_delete_employee(call):
        """Возвращает пользователя к выбору группы."""
        chat_id = call.message.chat.id

        if chat_id not in task_data or "group_index_map" not in task_data[chat_id]:
            bot.send_message(chat_id, "⚠ Ошибка: данные не найдены. Повторите команду /delete_user.")
            return

        group_index_map = task_data[chat_id]["group_index_map"]

        keyboard = InlineKeyboardMarkup()
        for index, group_name in group_index_map.items():
            keyboard.add(InlineKeyboardButton(group_name[:30], callback_data=f"delete_group_{index}"))

        bot.edit_message_text(
            "Выберите группу, из которой нужно удалить сотрудника:",
            chat_id,
            call.message.message_id,
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_user_"))
    def delete_employee(call):
        """Удаляет сотрудника из группы."""
        chat_id = call.message.chat.id
        user_id = int(call.data.split("_")[2])

        if chat_id not in task_data or "selected_group" not in task_data[chat_id]:
            bot.send_message(chat_id, "⚠ Ошибка: данные не найдены. Повторите команду /delete_user.")
            return

        group_name = task_data[chat_id]["selected_group"]

        if group_name not in config.performers:
            bot.send_message(chat_id, "⚠ Ошибка: группа не найдена.")
            return

        # Убираем inline-кнопки
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

        # Читаем config.py
        config_file = "config.py"
        with open(config_file, "r", encoding="utf-8") as file:
            config_content = file.readlines()

        # Определяем имя переменной с сотрудниками
        group_var_name = None
        for var_name, users in config.performers.items():
            if var_name == group_name:
                group_var_name = f"performers_list_{list(config.performers.keys()).index(var_name) + 1}"
                break

        if not group_var_name:
            bot.send_message(chat_id, f"⚠ Ошибка: группа <b>{group_name}</b> не найдена в config.py", parse_mode="HTML")
            return

        # Обновляем список сотрудников
        new_config_content = []
        group_updated = False

        for line in config_content:
            if line.strip().startswith(f"{group_var_name} ="):
                match = re.search(r"\((.*?)\)", line)
                if match:
                    existing_ids = match.group(1).strip()
                    existing_ids_list = [int(x.strip()) for x in existing_ids.split(",") if x.strip().isdigit()]
                else:
                    existing_ids_list = []

                if user_id not in existing_ids_list:
                    bot.send_message(chat_id, f"⚠ Пользователь с ID <b>{user_id}</b> не найден в группе {group_name}.",
                                     parse_mode="HTML")
                    return

                # Удаляем пользователя
                existing_ids_list.remove(user_id)
                updated_ids = ", ".join(map(str, existing_ids_list))

                new_config_content.append(
                    f"{group_var_name} = ({updated_ids},)\n" if updated_ids else f"{group_var_name} = ()\n")

                group_updated = True
            else:
                new_config_content.append(line)

        if not group_updated:
            bot.send_message(chat_id, f"⚠ Ошибка: список сотрудников группы <b>{group_name}</b> не найден в config.py",
                             parse_mode="HTML")
            return

        # Записываем обновленный config.py
        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(new_config_content)

        importlib.reload(config)

        bot.send_message(
            chat_id,
            f"✅ Пользователь с ID <b>{user_id}</b> удален из группы <b>{group_name}</b>!",
            parse_mode="HTML"
        )

        del task_data[chat_id]