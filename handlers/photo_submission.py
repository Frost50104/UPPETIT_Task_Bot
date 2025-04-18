import telebot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import config
from bot_instance import task_data
from task_storage import update_task_status, load_tasks, log_task_action
from users_cache import get_user_from_cache

def handle_photo_submission(bot):
    """Регистрация обработки фото от исполнителей и контрольной панели"""

    @bot.message_handler(content_types=['photo'])
    def receive_photo(message: Message):
        user_id = message.from_user.id

        # Проверка, что пользователь в контрольной панели
        if user_id not in sum(config.control_panel.keys(), ()):
            bot.send_message(message.chat.id, "⛔ Вы не числитесь в контрольной панели.", parse_mode="HTML")
            return

        # Обязательное условие — фото должно быть отправлено как ответ
        if not message.reply_to_message:
            bot.send_message(message.chat.id, "⚠ Пожалуйста, отправьте фото ответом на сообщение с задачей.")
            return

        original_message_id = message.reply_to_message.message_id
        tasks = load_tasks()
        uid = str(user_id)

        if uid not in tasks:
            bot.send_message(message.chat.id, "⚠ У вас нет активных задач.")
            return

        # Ищем по message_id и reminder_message_id:
        matching_task = next(
            (task for task in tasks[uid]
             if task["message_id"] == original_message_id or task.get("reminder_message_id") == original_message_id),
            None
        )
        if not matching_task:
            bot.send_message(message.chat.id, "⚠ Не удалось сопоставить фото с задачей. Убедитесь, что вы ответили на сообщение с заданием.")
            return

        photo = message.photo[-1].file_id
        task_text = matching_task["task_text"]
        first_name = message.from_user.first_name or f"ID: {user_id}"

        # Отправляем фото в контрольный чат
        sent_message = bot.send_photo(
            config.control_chat_id,
            photo,
            caption=f"📝 <b>Задача:</b> {task_text}\n👤 <b>{first_name}</b>",
            parse_mode="HTML"
        )

        # Добавляем inline-кнопки
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("✅ Принять",
                                 callback_data=f"accept_{sent_message.message_id}_{user_id}_{original_message_id}"),
            InlineKeyboardButton("❌ Отклонить",
                                 callback_data=f"reject_{sent_message.message_id}_{user_id}_{original_message_id}")
        )

        bot.edit_message_reply_markup(
            chat_id=config.control_chat_id,
            message_id=sent_message.message_id,
            reply_markup=keyboard
        )

        # Обновляем статус задачи
        update_task_status(user_id, original_message_id, "на утверждении", control_msg_id=sent_message.message_id)

        bot.send_message(message.chat.id, "✅ <b>Фото отправлено на проверку!</b>", parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith(("accept_", "reject_")))
    def process_verification(call: CallbackQuery):
        admin_id = call.from_user.id
        if admin_id not in config.ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Вы не можете одобрять или отклонять фото.")
            return

        try:
            action, control_msg_id, user_id, task_msg_id = call.data.split("_")
            control_msg_id = int(control_msg_id)
            user_id = int(user_id)
            task_msg_id = int(task_msg_id)
        except ValueError:
            bot.answer_callback_query(call.id, "⚠ Неверный формат данных.")
            return

        # Удаляем клавиатуру
        try:
            bot.edit_message_reply_markup(chat_id=config.control_chat_id, message_id=control_msg_id, reply_markup=None)
        except telebot.apihelper.ApiTelegramException:
            pass  # сообщение уже отредактировано

        if action == "accept":
            update_task_status(user_id, task_msg_id, "выполнена")
            admin_name = call.from_user.first_name or f"ID {call.from_user.id}"
            log_task_action(user_id, task_msg_id, action, get_user_from_cache, admin_name)
            bot.send_message(user_id, "✅ Фото принято! Спасибо за выполнение задачи.", parse_mode="HTML")
            bot.answer_callback_query(call.id, "Фото принято!")
        elif action == "reject":
            update_task_status(user_id, task_msg_id, "не выполнена")
            admin_name = call.from_user.first_name or f"ID {call.from_user.id}"
            log_task_action(user_id, task_msg_id, action, get_user_from_cache, admin_name)
            bot.send_message(user_id, "❌ Фото не принято. Пожалуйста, переделайте задачу и отправьте новое фото, ответив на сообщение с задачей.", parse_mode="HTML", reply_to_message_id=task_msg_id)
            bot.answer_callback_query(call.id, "Фото отклонено!")

    @bot.message_handler(
        func=lambda msg: msg.chat.id == config.control_chat_id and
                         msg.reply_to_message and
                         msg.reply_to_message.photo is not None
    )
    def handle_reply_comment(message: Message):
        replied_msg_id = message.reply_to_message.message_id
        admin_id = message.from_user.id
        comment_text = message.text.strip()

        tasks = load_tasks()

        for uid, user_tasks in tasks.items():
            for task in user_tasks:
                if task.get("control_msg_id") == replied_msg_id:
                    user_id = int(uid)
                    task_msg_id = task["message_id"]

                    # Обновляем статус
                    update_task_status(user_id, task_msg_id, "не выполнена")
                    admin_name = message.from_user.first_name or f"ID {admin_id}"
                    log_task_action(user_id, task_msg_id, "reject", get_user_from_cache, admin_name)

                    # Сообщение сотруднику
                    bot.send_message(
                        user_id,
                        "❌ Фото не принято. Пожалуйста, переделайте задачу и отправьте новое фото, ответив на сообщение с задачей.",
                        parse_mode="HTML",
                        reply_to_message_id=task_msg_id
                    )

                    # Комментарий
                    bot.send_message(
                        user_id,
                        f"💬 Комментарий модератора:\n<blockquote>{comment_text}</blockquote>",
                        parse_mode="HTML"
                    )

                    # ❌ Удаляем inline-кнопки у фото
                    try:
                        bot.edit_message_reply_markup(
                            chat_id=config.control_chat_id,
                            message_id=replied_msg_id,
                            reply_markup=None
                        )
                    except Exception as e:
                        print(f"⚠ Не удалось удалить клавиатуру у фото: {e}")

                    # ✅ Подтверждение в чат контроля
                    try:
                        bot.send_message(
                            config.control_chat_id,
                            "✅ Комментарий отправлен исполнителю.",
                            parse_mode="HTML",
                            reply_to_message_id=message.message_id
                        )
                    except Exception as e:
                        print(f"⚠ Не удалось отправить подтверждение в чат: {e}")

                    return