import telebot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import config

def handle_photo_submission(bot, task_data):
    """Регистрация обработки фото от исполнителей и контрольной панели"""
    # ========= Получение фото от исполнителя =========
    @bot.message_handler(content_types=['photo'])
    def receive_photo(message):
        user_id = message.from_user.id
        if user_id not in sum(config.control_panel.keys(), ()):  # Проверка, что исполнитель из одной из групп
            bot.send_message(message.chat.id, "⛔ Вы не числитесь в контрольной панели.", parse_mode="HTML")
            return

        photo = message.photo[-1].file_id

        # Попытаемся получить текст задачи для исполнителя; если нет — используем заглушку.
        task_text = task_data.get(user_id, {}).get("task_text", "_")
        first_name = message.from_user.first_name or f"ID: {user_id}"

        # Отправляем фото в контрольный чат без inline-кнопок для получения ID сообщения
        sent_message = bot.send_photo(
            config.control_chat_id,
            photo,
            caption=f"📝 <b>Задача:</b> {task_text}\n👤 <b>{first_name}</b>",
            parse_mode="HTML"
        )

        # Формируем inline-клавиатуру с кнопками "✅ Принять" и "❌ Отклонить"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{sent_message.message_id}_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{sent_message.message_id}_{user_id}")
        )

        # Редактируем сообщение в контрольном чате, добавляя клавиатуру
        bot.edit_message_reply_markup(chat_id=config.control_chat_id, message_id=sent_message.message_id,
                                      reply_markup=keyboard)

        # Сохраняем данные о сообщении в task_data (ключ – ID сообщения в контрольном чате)
        task_data[sent_message.message_id] = {
            "user_id": user_id,
            "user_message_id": message.message_id,
            "control_chat_id": config.control_chat_id,
            "task_text": task_text
        }

        # Подтверждаем пользователю, что фото отправлено
        bot.send_message(message.chat.id, "✅ <b>Фото отправлено на проверку!</b>", parse_mode="HTML")

    # ========= Обработка нажатий в контрольном чате =========
    @bot.callback_query_handler(func=lambda call: call.data.startswith(("accept_", "reject_")))
    def process_verification(call):
        admin_id = call.from_user.id
        if not admin_id in config.ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Вы не можете одобрять или отклонять фото.")
            return
        action, control_msg_id, user_id = call.data.split("_")
        control_msg_id = int(control_msg_id)
        user_id = int(user_id)
        if control_msg_id not in task_data:
            bot.answer_callback_query(call.id, "⚠ Данные не найдены.")
            return
        stored = task_data[control_msg_id]
        try:
            bot.edit_message_reply_markup(chat_id=stored["control_chat_id"], message_id=control_msg_id,
                                          reply_markup=None)
        except telebot.apihelper.ApiTelegramException:
            bot.answer_callback_query(call.id, "⚠ Ошибка: сообщение уже изменено или удалено.")
            return
        if action == "accept":
            bot.send_message(
                user_id,
                "Фото принято! Спасибо",
                reply_to_message_id=stored["user_message_id"],
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "Фото принято!")
            del task_data[control_msg_id]
        elif action == "reject":
            bot.send_message(
                user_id,
                "Фото не принято. Переделайте!",
                reply_to_message_id=stored["user_message_id"],
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "Фото отклонено!")
            del task_data[control_msg_id]
            request_new_photo(bot, user_id)

# ========= Запрос нового фото =========
def request_new_photo(bot, user_id):
    bot.send_message(user_id, "📷 Отправьте новое фото выполнения.")
