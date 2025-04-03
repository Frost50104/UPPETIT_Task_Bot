# Обработчик команды set_group_name
import re
import importlib
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import config

# Словарь для хранения соответствия индексов и имен групп
group_index_map = {str(index): name for index, name in enumerate(config.performers.keys())}

def handle_cmnd_set_group_name(bot, is_admin):
    """Регистрация обработчиков команды /set_group_name"""

    @bot.message_handler(commands=['set_group_name'])
    def set_group_name(message: Message):
        """Запускает процесс изменения названия группы."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять названия групп.")
            return

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="confirm_set_group_name"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_set_group_name")
        )

        bot.send_message(
            message.chat.id,
            "Хотите изменить название группы?",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_set_group_name")
    def cancel_set_group_name(call):
        """Обрабатывает отказ от изменения названия группы."""
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "🚫 Смена названия группы отменена.")

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_set_group_name")
    def process_set_group_name_choice(call):
        """Обрабатывает выбор администратора (изменять название или нет)."""
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав изменять названия групп.")
            return

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        importlib.reload(config)  # Обновляем данные

        global group_index_map
        group_index_map = {str(index): name for index, name in enumerate(config.performers.keys())}

        keyboard = InlineKeyboardMarkup()
        for index, group_name in group_index_map.items():
            keyboard.add(InlineKeyboardButton(group_name, callback_data=f"select_group_to_rename|{index}"))

        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_group_rename"))

        bot.send_message(
            call.message.chat.id,
            "Выберите группу, у которой хотите изменить имя:",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_group_rename")
    def cancel_group_rename(call):
        """Обрабатывает отмену выбора группы."""
        bot.edit_message_text("❌ Операция переименования группы отменена.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_group_to_rename"))
    def select_group_to_rename(call):
        """Сохраняет выбранную группу и запрашивает новое имя."""
        _, group_index = call.data.split("|")

        importlib.reload(config)
        group_index_map = {str(index): name for index, name in enumerate(config.performers.keys())}

        old_group_name = group_index_map.get(group_index)

        if not old_group_name or old_group_name not in config.performers:
            bot.send_message(call.message.chat.id, "⚠ Ошибка: группа не найдена.", parse_mode="HTML")
            return

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        bot.send_message(
            call.message.chat.id,
            f"Введите новое название для группы <b>{old_group_name}</b>:",
            parse_mode="HTML"
        )

        bot.register_next_step_handler(call.message, process_new_group_name, old_group_name)

    def process_new_group_name(message, old_group_name):
        """Обновляет название группы в config.py."""
        chat_id = message.chat.id
        new_group_name = message.text.strip()

        if not new_group_name:
            bot.send_message(chat_id, "⚠ Ошибка: название группы не может быть пустым. Повторите команду /set_group_name.")
            return

        config_file = "config.py"
        with open(config_file, "r", encoding="utf-8") as file:
            config_content = file.readlines()

        new_config_content = []
        group_updated = False

        for line in config_content:
            if line.strip().startswith("performers = {"):
                new_config_content.append(line)
                continue

            match = re.match(r"\s*'(.*?)':\s*(performers_list_\d+),", line)
            if match:
                current_group_name, group_var = match.groups()
                if current_group_name == old_group_name:
                    new_config_content.append(f"    '{new_group_name}': {group_var},\n")
                    group_updated = True
                    continue

            new_config_content.append(line)

        if not group_updated:
            bot.send_message(chat_id, f"⚠ Ошибка: группа <b>{old_group_name}</b> не найдена в config.py", parse_mode="HTML")
            return

        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(new_config_content)

        importlib.reload(config)

        bot.send_message(
            chat_id,
            f"✅ Название группы <b>{old_group_name}</b> изменено на <b>{new_group_name}</b>!",
            parse_mode="HTML"
        )

        updated_groups = "\n".join([f"🔹 <b>{group}</b>" for group in config.performers.keys()])
        bot.send_message(
            chat_id,
            f"🔄 <b>Обновленный список групп:</b>\n{updated_groups}",
            parse_mode="HTML"
        )