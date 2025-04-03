# Обработчик комнады /add_user
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
import importlib
import config
from bot_instance import bot, is_admin, task_data


def handle_cmnd_add_user(bot, is_admin, task_data):
    """Регистрация обработчиков команды /add_user"""
    # ========= Команда /add_user =========
    @bot.message_handler(commands=['add_user'])
    def handle_add_user(message):
        """Запускает процесс добавления нового сотрудника."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав для добавления сотрудников.")
            return

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="confirm_add_user"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_add_user")
        )

        bot.send_message(
            message.chat.id,
            "Хотите добавить нового пользователя?",
            parse_mode="HTML",
            reply_markup=keyboard
        )


    @bot.callback_query_handler(func=lambda call: call.data in ["confirm_add_user", "cancel_add_user"])
    def process_add_user_choice(call):
        """Обрабатывает выбор администратора (добавлять или нет)."""
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав изменять список сотрудников.")
            return

        if call.data == "cancel_add_user":
            bot.edit_message_text("❌ Добавление пользователя отменено.", call.message.chat.id, call.message.message_id)
            return

        # Перезагружаем config перед созданием кнопок
        importlib.reload(config)

        keyboard = InlineKeyboardMarkup()
        group_index_map = {str(index): group for index, group in enumerate(config.performers.keys())}

        for index, group_name in group_index_map.items():
            keyboard.add(InlineKeyboardButton(group_name[:30], callback_data=f"select_group_{index}"))

        # Добавляем кнопку "Отмена" под всеми группами
        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_group_selection"))

        bot.edit_message_text(
            "Выберите группу, в которую нужно добавить нового сотрудника:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )

        # Сохраняем соответствие индексов и названий групп
        task_data[call.message.chat.id] = {"group_index_map": group_index_map}


    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_group_"))
    def select_group(call):
        """Запрашивает ID нового сотрудника после выбора группы."""
        chat_id = call.message.chat.id
        group_index = call.data.split("_")[2]

        if chat_id not in task_data or "group_index_map" not in task_data[chat_id]:
            bot.send_message(chat_id, "⚠ Ошибка: данные не найдены. Повторите команду /add_user.")
            return

        # Получаем название группы по индексу
        group_name = task_data[chat_id]["group_index_map"].get(group_index)

        if not group_name:
            bot.send_message(chat_id, "⚠ Ошибка: группа не найдена.")
            return

        # Сохраняем выбранную группу
        task_data[chat_id]["selected_group"] = group_name

        bot.edit_message_text(
            f"Вы выбрали группу <b>{group_name}</b>\n\nУкажите ID сотрудника:",
            chat_id,
            call.message.message_id,
            parse_mode="HTML"
        )

        bot.register_next_step_handler_by_chat_id(chat_id, process_new_user_id)


    def process_new_user_id(message):
        """Добавляет нового сотрудника в config.py."""
        chat_id = message.chat.id

        if chat_id not in task_data or "selected_group" not in task_data[chat_id]:
            bot.send_message(chat_id, "⚠ Ошибка: группа не найдена. Повторите команду /add_user.")
            return

        try:
            new_user_id = int(message.text.strip())
        except ValueError:
            bot.send_message(chat_id, "⚠ Ошибка: ID должен быть числом. Попробуйте снова.", parse_mode="HTML")
            return

        group_name = task_data[chat_id]["selected_group"]

        # 🔄 Уведомляем о процессе
        loading_msg = bot.send_message(chat_id, "🔄 Обновление базы пользователей...", parse_mode="HTML")

        # Читаем config.py
        config_file = "config.py"
        with open(config_file, "r", encoding="utf-8") as file:
            config_content = file.readlines()

        # Определяем имя переменной с кортежем сотрудников
        group_var_name = None
        for var_name in config.performers.keys():
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

                if new_user_id in existing_ids_list:
                    try:
                        user_info = bot.get_chat(new_user_id)
                        user_name = user_info.first_name
                    except Exception:
                        user_name = f"ID {new_user_id}"
                    bot.send_message(chat_id, f"⚠ Пользователь <b>{user_name}</b> уже в группе {group_name}.",
                                     parse_mode="HTML")
                    return

                existing_ids_list.append(new_user_id)
                updated_ids = ", ".join(map(str, existing_ids_list))

                # Обновляем строку в файле
                new_config_content.append(f"{group_var_name} = ({updated_ids},)\n")
                group_updated = True
            else:
                new_config_content.append(line)

        if not group_updated:
            bot.send_message(chat_id, f"⚠ Ошибка: список сотрудников группы <b>{group_name}</b> не найден в config.py", parse_mode="HTML")
            return

        # Записываем обновленный config.py
        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(new_config_content)

        # Перезагружаем config.py
        importlib.reload(config)

        # 🔁 Обновляем кэш пользователей
        from users_cache import build_user_cache
        build_user_cache()

        try:
            user_info = bot.get_chat(new_user_id)
            user_name = user_info.first_name
        except Exception:
            user_name = f"ID {new_user_id}"

        bot.edit_message_text(
            f"✅ Пользователь <b>{user_name}</b> добавлен в группу <b>{group_name}</b>!\n\n✅ База пользователей обновлена.",
            chat_id=chat_id,
            message_id=loading_msg.message_id,
            parse_mode="HTML"
        )

        del task_data[chat_id]

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_group_selection")
    def cancel_group_selection(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав.")
            return

        bot.edit_message_text(
            "❌ Добавление пользователя отменено.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )

        # Очищаем временные данные, если есть
        task_data.pop(call.message.chat.id, None)

        bot.answer_callback_query(call.id)