import importlib
import config
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

def handle_cmnd_set_task_group(bot, is_admin, task_data, daily_tasks, weekly_tasks, monthly_tasks):
    """Регистрация обработчиков команды /set_task_group"""
    # ========= Команда /set_task_group =========
    @bot.message_handler(commands=['set_task_group'])
    def handle_set_task_group(message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Нет прав.")
            return

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("📅 Ежедневная", callback_data="select_task_type_daily"),
            InlineKeyboardButton("📆 Еженедельная", callback_data="select_task_type_weekly"),
            InlineKeyboardButton("🗓 Ежемесячная", callback_data="select_task_type_monthly")
        )
        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_task_group"))

        bot.send_message(
            message.chat.id,
            "Выберите рассылку, для которой хотите изменить задачи по группам:",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_task_type_"))
    def handle_task_type_selection(call):
        task_type = call.data.replace("select_task_type_", "")  # daily / weekly / monthly
        bot.answer_callback_query(call.id)

        keyboard = InlineKeyboardMarkup(row_width=2)
        for i, group_name in enumerate(config.performers.keys(), start=1):
            callback_data = f"edit_task_group_{task_type}_{i}"  # безопасно!
            keyboard.add(InlineKeyboardButton(group_name, callback_data=callback_data))

        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_task_group"))

        bot.edit_message_text(
            "Выберите группу, для которой нужно изменить задание:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_task_group_"))
    def handle_group_selection(call):
        parts = call.data.split("_")  # ["edit", "task", "group", "daily", "1"]
        task_type = parts[3]
        group_number = parts[4]
        bot.answer_callback_query(call.id)

        group_names = list(config.performers.keys())
        group_name = group_names[int(group_number) - 1]  # Название для вывода

        # Удаляем кнопки
        bot.edit_message_text(
            f"Введите новое задание для группы <b>{group_name}</b>:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            call.message,
            lambda m, tt=task_type, gn=group_number: update_single_task(m, tt, gn)
        )

    def update_named_task(message, task_type, group_name):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Нет прав.")
            return

        # Преобразуем название группы в ключ task_group_X
        group_index = list(config.performers.keys()).index(group_name) + 1
        key = f"task_group_{group_index}"

        block_name = {
            "daily": "daily_tasks",
            "weekly": "weekly_tasks",
            "monthly": "monthly_tasks"
        }[task_type]

        # Загрузим config.py
        with open("config.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Найдём и перезапишем словарь
        current_dict = {}
        inside = False
        dict_text = ""
        for line in lines:
            if line.strip().startswith(f"{block_name}"):
                inside = True
                dict_text = line[line.find("=") + 1:].strip()
                continue
            if inside:
                if line.strip().startswith("#") or "=" in line:
                    break
                dict_text += line

        try:
            current_dict = eval(dict_text)
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠ Ошибка при чтении словаря: {e}")
            return

        current_dict[key] = message.text.strip()
        new_dict_text = json.dumps(current_dict, indent=4, ensure_ascii=False)

        # Заменяем в config.py
        new_lines = []
        skipping = False
        for line in lines:
            if line.strip().startswith(f"{block_name}"):
                new_lines.append(f"{block_name} = {new_dict_text}\n")
                skipping = True
                continue
            if skipping:
                if line.strip().startswith("}") or "=" in line or line.strip().startswith("#"):
                    skipping = False
                continue
            new_lines.append(line)

        with open("config.py", "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        importlib.reload(config)
        bot.send_message(message.chat.id, "✅ Задание обновлено!")

    def update_single_task(message, task_type, group_number):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Нет прав.")
            return

        key = f"task_group_{group_number}"
        block_name = {
            "daily": "daily_tasks",
            "weekly": "weekly_tasks",
            "monthly": "monthly_tasks"
        }[task_type]

        with open("config.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Извлекаем текущий словарь
        current_dict = {}
        inside = False
        dict_text = ""
        for line in lines:
            if line.strip().startswith(f"{block_name}"):
                inside = True
                dict_text = line[line.find("=") + 1:].strip()
                continue
            if inside:
                if line.strip().startswith("#") or "=" in line:
                    break
                dict_text += line

        try:
            current_dict = eval(dict_text)
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠ Ошибка чтения текущего словаря: {e}")
            return

        # Обновляем ключ
        current_dict[key] = message.text.strip()
        formatted_dict = json.dumps(current_dict, indent=4, ensure_ascii=False)

        # Перезаписываем блок в файле
        new_lines = []
        inside = False
        for line in lines:
            if line.strip().startswith(f"{block_name}"):
                inside = True
                new_lines.append(f"{block_name} = {formatted_dict}\n")
                continue
            if inside:
                if line.strip().startswith("}") or line.strip().startswith("#") or "=" in line:
                    inside = False
                continue
            new_lines.append(line)

        with open("config.py", "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        importlib.reload(config)
        bot.send_message(message.chat.id, "✅ Задание обновлено!")

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_task_group")
    def cancel_task_group_edit(call):
        bot.answer_callback_query(call.id)
        bot.edit_message_text("❌ Изменение задания отменено.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_task"))
    def edit_task(call):
        """Запрашивает у администратора новое задание для выбранной группы."""
        _, chat_id, group_hash = call.data.split("|")
        chat_id = int(chat_id)

        if group_hash not in group_name_map:
            bot.answer_callback_query(call.id, "⚠ Ошибка: группа не найдена.")
            return

        group_name = group_name_map[group_hash]

        task_data[chat_id] = {"selected_group": group_name}

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        bot.send_message(chat_id, f"Введите новое задание для группы <b>{group_name}</b>:", parse_mode="HTML")
        bot.register_next_step_handler_by_chat_id(chat_id, update_task_text)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_set_tasks_group"))
    def cancel_set_tasks_group(call):
        """Отмена изменения заданий для групп."""
        chat_id = int(call.data.split("|")[1])

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(chat_id, "🚫 Изменение задач для автоматической отправки отменено.")

    def update_task_text(message):
        """Обновляет задание для выбранной группы в config.py и сохраняет его в control_panel_for_set_tasks_group."""
        chat_id = message.chat.id

        if chat_id not in task_data or "selected_group" not in task_data[chat_id]:
            bot.send_message(chat_id, "⚠ Ошибка: группа не найдена. Повторите команду /set_tasks_group.")
            return

        new_task_text = message.text.strip()
        group_name = task_data[chat_id]["selected_group"]

        config_file = "config.py"
        with open(config_file, "r", encoding="utf-8") as file:
            config_content = file.readlines()

        # Определяем переменную задания
        group_index = list(config.performers.keys()).index(group_name) + 1
        task_var_name = f"task_group_{group_index}"
        performers_key = f"performers_list_{group_index}"

        # Обновленный список строк конфигурации
        new_config_content = []
        inside_task_block = False
        task_updated = False

        for line in config_content:
            if line.strip().startswith(f"{task_var_name} = '''") or line.strip().startswith(f'{task_var_name} = """'):
                # Найден старый блок задачи — заменяем его
                new_config_content.append(f"{task_var_name} = '''\n{new_task_text}\n'''\n")
                inside_task_block = True
                task_updated = True
                continue

            if inside_task_block:
                if line.strip().endswith("'''") or line.strip().endswith('"""'):
                    inside_task_block = False  # Конец старого блока задачи
                continue  # Не записываем старые строки задачи

            new_config_content.append(line)  # Оставляем все остальные строки без изменений

        if not task_updated:
            bot.send_message(chat_id, f"⚠ Ошибка: переменная {task_var_name} не найдена в config.py")
            return

        # Записываем исправленный config.py
        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(new_config_content)

        # Перезагружаем config.py, чтобы бот сразу видел изменения
        importlib.reload(config)

        # Обновляем `control_panel_for_set_tasks_group`
        config.control_panel_for_set_tasks_group[performers_key] = new_task_text

        bot.send_message(
            chat_id,
            f"✅ Задание для группы <b>{group_name}</b> успешно обновлено!",
            parse_mode="HTML"
        )

        del task_data[chat_id]