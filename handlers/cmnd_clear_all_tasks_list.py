from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from task_storage import clear_all_tasks

def handle_cmnd_clear_all_tasks_list(bot, is_admin):
    """Регистрация команды /clear_all_tasks_list"""

    @bot.message_handler(commands=["clear_all_tasks_list"])
    def ask_clear_all_tasks(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к этой команде.", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="clear_all_tasks_confirm"),
            InlineKeyboardButton("❌ Нет", callback_data="clear_all_tasks_cancel")
        )

        bot.send_message(
            message.chat.id,
            "⚠ <b>Вы действительно хотите удалить все задачи</b> — независимо от их статуса?",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("clear_all_tasks_"))
    def handle_clear_all_confirmation(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Только для админов.")
            return

        if call.data == "clear_all_tasks_cancel":
            bot.edit_message_text(
                "🚫 <b>Полная очистка отменена.</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        elif call.data == "clear_all_tasks_confirm":
            clear_all_tasks()
            bot.edit_message_text(
                "✅ <b>Все задачи удалены.</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )

        bot.answer_callback_query(call.id)