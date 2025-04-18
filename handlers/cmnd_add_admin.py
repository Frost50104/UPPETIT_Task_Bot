
import importlib
import config
import re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from logger import log_action

def handle_cmnd_add_admin(bot, is_admin, task_data):
    """Регистрация обработчиков команды /add_admin"""
    # ========= Команда /add_admin =========
    @bot.message_handler(commands=['add_admin'])
    def handle_add_admin(message):
        """Запускает процесс добавления нового администратора."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав для добавления администраторов.")
            return

        # Перезагружаем config.py перед выводом списка администраторов
        importlib.reload(config)

        # Получаем список текущих администраторов
        admin_list = []
        for admin_id in config.ADMIN_ID:
            try:
                user = bot.get_chat(admin_id)
                username = f"@{user.username}" if user.username else f"ID: {admin_id}"
            except telebot.apihelper.ApiTelegramException:
                username = f"ID: {admin_id} (❌ не найден)"

            admin_list.append(f"👤 {username}")

        admin_text = "\n".join(admin_list) if admin_list else "❌ Нет администраторов."

        # Создаем inline-кнопки
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="confirm_add_admin"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_add_admin")
        )

        # Отправляем сообщение с HTML-разметкой
        bot.send_message(
            message.chat.id,
            f"🔹 <b>Список администраторов:</b>\n{admin_text}\n\n"
            "Хотите добавить нового администратора?",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # ========= Обработка выбора "Да" / "Нет" =========
    @bot.callback_query_handler(func=lambda call: call.data in ["confirm_add_admin", "cancel_add_admin"])
    def process_add_admin_choice(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав изменять администраторов.")
            return

        if call.data == "confirm_add_admin":
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, "✏ Укажите ID нового администратора:")
            bot.register_next_step_handler(call.message, process_admin_id)

        elif call.data == "cancel_add_admin":
            bot.edit_message_text("❌ Добавление администратора отменено.", call.message.chat.id,
                                  call.message.message_id)

    # ========= Обработка ID нового администратора =========
    def process_admin_id(message):
        """Добавляет новый ID администратора в список `ADMIN_ID` в `config.py`."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав изменять администраторов.")
            return

        try:
            new_admin_id = int(message.text.strip())  # Преобразуем введенное значение в int
        except ValueError:
            bot.send_message(message.chat.id,
                             "⚠ Ошибка: ID должен быть числом. Попробуйте снова с командой /add_admin.")
            return

        # Читаем config.py
        config_file = "config.py"
        with open(config_file, "r", encoding="utf-8") as file:
            config_content = file.readlines()

        # Проверяем, есть ли уже этот админ в списке
        if new_admin_id in config.ADMIN_ID:
            bot.send_message(
                message.chat.id,
                f"⚠ Пользователь с ID <code>{new_admin_id}</code> уже является администратором.",
                parse_mode="HTML"
            )
            return

        # Обновляем `ADMIN_ID`
        for i, line in enumerate(config_content):
            if line.strip().startswith("ADMIN_ID"):
                match = re.search(r"\[(.*?)\]", line)
                if match:
                    existing_ids = match.group(1).strip()
                    existing_ids_list = [int(x.strip()) for x in existing_ids.split(",") if x.strip().isdigit()]
                else:
                    existing_ids_list = []

                # Добавляем нового администратора
                existing_ids_list.append(new_admin_id)
                updated_ids = ", ".join(map(str, existing_ids_list))

                # Обновляем строку в файле
                config_content[i] = f"ADMIN_ID = [{updated_ids}]\n"
                break
        else:
            bot.send_message(message.chat.id, "⚠ Ошибка: не найден список администраторов в config.py",
                             parse_mode="HTML")
            return

        # Записываем обновленный config.py
        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(config_content)

        # Перезагружаем config.py, чтобы бот сразу видел изменения
        importlib.reload(config)

        # Log the action with the added admin ID
        log_action(
            user_id=message.from_user.id,
            action="Добавил нового администратора",
            details=f"ID добавленного администратора: {new_admin_id}",
            admin_name=message.from_user.first_name
        )

        bot.send_message(
            message.chat.id,
            f"✅ Пользователь с ID <code>{new_admin_id}</code> добавлен в список администраторов.",
            parse_mode="HTML"
        )
