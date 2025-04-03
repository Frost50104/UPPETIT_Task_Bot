
import importlib
import config
import re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def handle_cmnd_delete_admin(bot, is_admin):
    """Регистрация обработчиков команды /delete_admin"""

    # ========= Команда /delete_admin =========
    @bot.message_handler(commands=['delete_admin'])
    def handle_delete_admin(message):
        """Запускает процесс удаления администратора."""
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав для удаления администраторов.")
            return

        # Создаем inline-кнопки
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="confirm_delete_admin"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_delete_admin")
        )

        bot.send_message(message.chat.id, "Хотите удалить администратора?", reply_markup=keyboard)

    # ========= Обработка выбора "Да" / "Нет" =========
    @bot.callback_query_handler(func=lambda call: call.data in ["confirm_delete_admin", "cancel_delete_admin"])
    def process_delete_admin_choice(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав изменять администраторов.")
            return

        if call.data == "confirm_delete_admin":
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

            # Перезагружаем config.py перед выводом списка администраторов
            importlib.reload(config)

            # Получаем список текущих администраторов
            keyboard = InlineKeyboardMarkup()
            admin_list = []

            for admin_id in config.ADMIN_ID:
                if admin_id == call.from_user.id:
                    continue  # Администратор не может удалить сам себя!

                try:
                    user = bot.get_chat(admin_id)
                    username = f"@{user.username}" if user.username else "Без username"
                    first_name = user.first_name or "Без имени"
                    display_text = f"👤 {first_name} ({username}) - {admin_id}"
                except telebot.apihelper.ApiTelegramException:
                    display_text = f"❌ ID: {admin_id} (не найден)"

                admin_list.append(display_text)
                keyboard.add(InlineKeyboardButton(display_text, callback_data=f"delete_admin_{admin_id}"))

            # Добавляем кнопку "❌ Отмена"
            keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete_admin"))

            if not admin_list:
                bot.send_message(call.message.chat.id, "⚠ Нет доступных администраторов для удаления.",
                                 parse_mode="HTML")
                return

            bot.send_message(
                call.message.chat.id,
                "Выберите администратора для удаления:\n" + "\n".join(admin_list),
                parse_mode="HTML",
                reply_markup=keyboard
            )

        elif call.data == "cancel_delete_admin":
            bot.edit_message_text("❌ Удаление администратора отменено.", call.message.chat.id, call.message.message_id)

    # ========= Удаление администратора и обновление config.py =========
    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_admin_"))
    def process_admin_deletion(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ У вас нет прав изменять администраторов.")
            return

        try:
            admin_id_to_delete = int(call.data.split("_")[2])
        except ValueError:
            bot.send_message(call.message.chat.id, "⚠ Ошибка: некорректный формат ID администратора.",
                             parse_mode="HTML")
            return

        if admin_id_to_delete == call.from_user.id:
            bot.send_message(call.message.chat.id, "⛔ Вы не можете удалить сами себя!", parse_mode="HTML")
            return

        # Удаляем inline-кнопки после выбора администратора
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        # Читаем config.py
        config_file = "config.py"
        with open(config_file, "r", encoding="utf-8") as file:
            config_content = file.readlines()

        # Удаление администратора из ADMIN_ID
        for i, line in enumerate(config_content):
            if line.strip().startswith("ADMIN_ID"):
                match = re.search(r"\[(.*?)\]", line)
                if match:
                    existing_ids = match.group(1).strip()
                    existing_ids_list = [int(x.strip()) for x in existing_ids.split(",") if x.strip().isdigit()]
                else:
                    existing_ids_list = []

                if admin_id_to_delete not in existing_ids_list:
                    bot.send_message(call.message.chat.id, f"⚠ Администратор с ID {admin_id_to_delete} не найден.",
                                     parse_mode="HTML")
                    return

                # Удаляем администратора из списка
                existing_ids_list.remove(admin_id_to_delete)
                updated_ids = ", ".join(map(str, existing_ids_list))

                # Обновляем строку в файле
                config_content[i] = f"ADMIN_ID = [{updated_ids}]\n"
                break
        else:
            bot.send_message(call.message.chat.id, "⚠ Ошибка: не найден список администраторов в config.py",
                             parse_mode="HTML")
            return

        # Записываем обновленный config.py
        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(config_content)

        # Перезагружаем config.py, чтобы бот сразу видел изменения
        importlib.reload(config)

        bot.send_message(
            call.message.chat.id,
            f"✅ Администратор с ID <code>{admin_id_to_delete}</code> удален.",
            parse_mode="HTML"
        )