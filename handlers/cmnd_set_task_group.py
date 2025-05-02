import importlib
import config
import json
import hashlib
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Словарь для хранения хешей групп
group_name_map = {}

# Генерация короткого хеша
def hash_name(name):
    return hashlib.md5(name.encode()).hexdigest()[:10]

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

        # 🔄 Обновим config (гарантированно получим свежие данные)
        importlib.reload(config)

        # Выбираем нужный словарь из config
        task_dict = {
            "daily": config.daily_tasks,
            "weekly": config.weekly_tasks,
            "monthly": config.monthly_tasks
        }[task_type]

        # Сохраняем выбранный тип рассылки в task_data
        cid = call.message.chat.id
        if cid not in task_data:
            task_data[cid] = {}
        task_data[cid]["task_type"] = task_type
        task_data[cid]["selected_groups"] = []

        # Получаем текущую задачу для этого типа рассылки
        current_task = "❌ Нет задания"
        for key, value in task_dict.items():
            if key.startswith("task_group_"):
                current_task = value
                break

        # Получаем список групп, участвующих в рассылке
        participating_groups = []
        for i, group_name in enumerate(config.performers.keys(), start=1):
            key = f"task_group_{i}"
            if key in task_dict:
                participating_groups.append(group_name)

        # Формируем сообщение
        message_text = f"<b>Текущая задача для {task_type} рассылки:</b>\n{current_task}\n\n"
        if participating_groups:
            message_text += "<b>Группы, участвующие в рассылке:</b>\n"
            for group in participating_groups:
                message_text += f"• {group}\n"
        else:
            message_text += "<b>Нет групп, участвующих в рассылке</b>"

        # Создаем клавиатуру с кнопками "Группы" и "Задача"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("👥 Группы", callback_data=f"set_task_groups_{task_type}"),
            InlineKeyboardButton("📝 Задача", callback_data=f"set_task_text_{task_type}")
        )
        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_task_group"))

        # Редактируем исходное сообщение
        bot.edit_message_text(
            message_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("set_task_groups_"))
    def handle_set_task_groups(call):
        task_type = call.data.replace("set_task_groups_", "")  # daily / weekly / monthly
        bot.answer_callback_query(call.id)
        cid = call.message.chat.id

        # Сохраняем выбранный тип рассылки в task_data, если еще не сохранен
        if cid not in task_data:
            task_data[cid] = {}
        task_data[cid]["task_type"] = task_type
        if "selected_groups" not in task_data[cid]:
            task_data[cid]["selected_groups"] = []

        # Редактируем сообщение
        bot.edit_message_text(
            "Выберите получателей:",
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=None
        )

        # Отправляем список групп
        send_group_selection_buttons(cid, call.message.message_id)

    def send_group_selection_buttons(cid, message_id=None):
        """Отправляет кнопки с группами для выбора получателей"""
        importlib.reload(config)
        selected_groups = task_data[cid]["selected_groups"]

        # Создаем клавиатуру с группами
        keyboard = InlineKeyboardMarkup(row_width=1)  # По одной кнопке в строке из-за возможной длины названий

        # Добавляем кнопки для групп, которые еще не выбраны
        for group_name in config.performers:
            if group_name not in selected_groups:
                h = hash_name(group_name)
                group_name_map[h] = group_name
                keyboard.add(InlineKeyboardButton(group_name, callback_data=f"select_group|{h}"))

        # Добавляем кнопку "Завершить добавление"
        keyboard.add(InlineKeyboardButton("✅ Завершить добавление", callback_data="finish_group_selection"))

        # Если есть ID сообщения, редактируем его, иначе отправляем новое
        if message_id:
            bot.edit_message_reply_markup(
                chat_id=cid,
                message_id=message_id,
                reply_markup=keyboard
            )
        else:
            # Формируем текст с выбранными группами
            if selected_groups:
                text = "Выбранные группы:\n"
                for group in selected_groups:
                    text += f"• {group}\n"
                text += "\nВыберите еще получателей или нажмите 'Завершить добавление':"
            else:
                text = "Выберите получателей:"

            bot.send_message(
                cid,
                text,
                reply_markup=keyboard
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_group|"))
    def handle_group_selection(call):
        _, group_hash = call.data.split("|")
        cid = call.message.chat.id
        bot.answer_callback_query(call.id)

        # Получаем название группы по хешу
        group_name = group_name_map.get(group_hash)
        if not group_name:
            bot.send_message(cid, "⚠️ Ошибка: группа не найдена")
            return

        # Добавляем группу в список выбранных
        if cid in task_data and "selected_groups" in task_data[cid]:
            if group_name not in task_data[cid]["selected_groups"]:
                task_data[cid]["selected_groups"].append(group_name)

        # Обновляем кнопки
        send_group_selection_buttons(cid, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "finish_group_selection")
    def handle_finish_group_selection(call):
        cid = call.message.chat.id
        bot.answer_callback_query(call.id)

        if cid not in task_data or "task_type" not in task_data[cid]:
            bot.send_message(cid, "⚠️ Ошибка: тип рассылки не выбран")
            return

        task_type = task_data[cid]["task_type"]
        selected_groups = task_data[cid].get("selected_groups", [])

        # Формируем сообщение с выбранными группами
        if selected_groups:
            message_text = f"<b>Выбранные группы для {task_type} рассылки:</b>\n"
            for group in selected_groups:
                message_text += f"• {group}\n"
        else:
            message_text = f"<b>Не выбрано ни одной группы для {task_type} рассылки</b>"

        # Получаем текущую задачу
        task_dict = {
            "daily": config.daily_tasks,
            "weekly": config.weekly_tasks,
            "monthly": config.monthly_tasks
        }[task_type]

        current_task = "❌ Нет задания"
        for key, value in task_dict.items():
            if key.startswith("task_group_"):
                current_task = value
                break

        # Определяем блок задач в config.py
        block_name = {
            "daily": "daily_tasks",
            "weekly": "weekly_tasks",
            "monthly": "monthly_tasks"
        }[task_type]

        # Загружаем config.py
        with open("config.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Извлекаем текущий словарь задач
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
            bot.send_message(cid, f"⚠ Ошибка при чтении словаря: {e}")
            return

        # Сначала очищаем все группы (устанавливаем значение None для всех task_group_X)
        for i in range(1, len(config.performers.keys()) + 1):
            key = f"task_group_{i}"
            if key in current_dict:
                current_dict[key] = None

        # Затем устанавливаем текущую задачу только для выбранных групп
        for group_name in selected_groups:
            try:
                group_index = list(config.performers.keys()).index(group_name) + 1
                key = f"task_group_{group_index}"
                current_dict[key] = current_task
            except ValueError:
                bot.send_message(cid, f"⚠ Ошибка: группа {group_name} не найдена")
                continue

        # Удаляем None значения
        keys_to_remove = [k for k, v in current_dict.items() if v is None]
        for key in keys_to_remove:
            del current_dict[key]

        # Форматируем обновленный словарь
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

        # Перезагружаем config.py
        importlib.reload(config)

        message_text += f"\n\n<b>Текущая задача:</b>\n{current_task}"
        message_text += f"\n\n✅ Список получателей успешно обновлен!"

        # Редактируем сообщение без клавиатуры
        bot.edit_message_text(
            message_text,
            chat_id=cid,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )

        # Очищаем данные задачи для завершения обработчика
        if cid in task_data:
            del task_data[cid]



    @bot.callback_query_handler(func=lambda call: call.data == "cancel_task_group")
    def cancel_task_group_edit(call):
        bot.answer_callback_query(call.id)
        bot.edit_message_text("❌ Изменение задания отменено.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("set_task_text_"))
    def handle_set_task_text(call):
        """Запрашивает у администратора новое задание для выбранного типа рассылки."""
        task_type = call.data.replace("set_task_text_", "")  # daily / weekly / monthly
        cid = call.message.chat.id
        bot.answer_callback_query(call.id)

        # Сохраняем выбранный тип рассылки в task_data, если еще не сохранен
        if cid not in task_data:
            task_data[cid] = {}
        task_data[cid]["task_type"] = task_type

        # Редактируем сообщение
        bot.edit_message_text(
            "Введите текст задачи:",
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=None
        )

        # Регистрируем обработчик для следующего сообщения
        bot.register_next_step_handler_by_chat_id(cid, handle_new_task_text)


    def handle_new_task_text(message):
        """Обновляет задание для выбранных групп в config.py."""
        chat_id = message.chat.id

        if chat_id not in task_data or "task_type" not in task_data[chat_id]:
            bot.send_message(chat_id, "⚠ Ошибка: тип рассылки не выбран. Повторите команду /set_task_group.")
            return

        new_task_text = message.text.strip()
        task_type = task_data[chat_id]["task_type"]
        selected_groups = task_data[chat_id].get("selected_groups", [])

        # Если группы не выбраны, используем только те группы, которые уже участвуют в рассылке
        if not selected_groups:
            # Определяем блок задач в config.py
            block_name = {
                "daily": "daily_tasks",
                "weekly": "weekly_tasks",
                "monthly": "monthly_tasks"
            }[task_type]

            # Загружаем config.py
            with open("config.py", "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Извлекаем текущий словарь задач
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
                bot.send_message(chat_id, f"⚠ Ошибка при чтении словаря: {e}")
                return

            # Получаем список групп, участвующих в рассылке
            participating_groups = []
            for i, group_name in enumerate(config.performers.keys(), start=1):
                key = f"task_group_{i}"
                if key in current_dict:
                    participating_groups.append(group_name)

            selected_groups = participating_groups

        # Определяем блок задач в config.py
        block_name = {
            "daily": "daily_tasks",
            "weekly": "weekly_tasks",
            "monthly": "monthly_tasks"
        }[task_type]

        # Загружаем config.py
        with open("config.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Извлекаем текущий словарь задач
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
            bot.send_message(chat_id, f"⚠ Ошибка при чтении словаря: {e}")
            return

        # Обновляем задачи для выбранных групп
        for group_name in selected_groups:
            group_index = list(config.performers.keys()).index(group_name) + 1
            key = f"task_group_{group_index}"
            current_dict[key] = new_task_text

        # Форматируем обновленный словарь
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

        # Перезагружаем config.py
        importlib.reload(config)

        # Обновляем control_panel_for_set_tasks_group для выбранных групп
        for group_name in selected_groups:
            group_index = list(config.performers.keys()).index(group_name) + 1
            performers_key = f"performers_list_{group_index}"
            config.control_panel_for_set_tasks_group[performers_key] = new_task_text

        # Формируем сообщение об успешном обновлении
        if len(selected_groups) == 1:
            success_message = f"✅ Задание для группы <b>{selected_groups[0]}</b> успешно обновлено!"
        else:
            success_message = f"✅ Задание для <b>{len(selected_groups)} групп</b> успешно обновлено!"

        bot.send_message(
            chat_id,
            success_message,
            parse_mode="HTML"
        )

        # Очищаем данные задачи
        del task_data[chat_id]
