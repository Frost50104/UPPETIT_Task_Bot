from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from task_storage import load_tasks, set_reminder_message_id

def handle_cmnd_arbeiten(bot, is_admin):
    @bot.message_handler(commands=["arbeiten"])
    def arbeiten_prompt(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к этой команде.", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="arbeiten_confirm"),
            InlineKeyboardButton("❌ Нет", callback_data="arbeiten_cancel")
        )

        bot.send_message(
            message.chat.id,
            "🔨 Пнуть тех, кто не выполнил задание?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("arbeiten_"))
    def arbeiten_confirm_handler(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Только для админов.")
            return

        if call.data == "arbeiten_cancel":
            bot.edit_message_text(
                "😌 Пинание отменено.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
            bot.answer_callback_query(call.id)
            return

        if call.data == "arbeiten_confirm":
            tasks = load_tasks()

            # Собираем всех, кого надо пнуть
            to_notify = []
            for uid, task_list in tasks.items():
                for task in task_list:
                    if task["status"] == "не выполнена":
                        to_notify.append((uid, task))

            if not to_notify:
                bot.edit_message_text(
                    "✅ Все молодцы, все задачи выполнены!",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode="HTML"
                )
                bot.answer_callback_query(call.id)
                return

            # Иначе — пинаем
            bot.edit_message_text(
                "🚀 Отправляем напоминания нарушителям!",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )

            notified = 0

            for uid, task in to_notify:
                try:
                    uid_int = int(uid)

                    bot.send_message(
                        uid_int,
                        "❗ <b>ВЫ ПРОИГНОРИРОВАЛИ ПОСТАВЛЕННУЮ ЗАДАЧУ, ОДУМАЙТЕСЬ!</b>",
                        parse_mode="HTML"
                    )

                    msg = bot.send_message(
                        uid_int,
                        f"📌 <b>Задание (повторно):</b>\n{task['task_text']}",
                        parse_mode="HTML"
                    )

                    set_reminder_message_id(uid_int, task["message_id"], msg.message_id)

                    notified += 1
                except Exception as e:
                    print(f"⚠ Не удалось отправить повторную задачу {uid}: {e}")

            bot.answer_callback_query(call.id, f"Пнуты {notified} нарушителей.")