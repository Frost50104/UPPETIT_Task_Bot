from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from task_storage import clear_completed_tasks as clear_all_tasks

def handle_cmnd_clear_tasks_list(bot, is_admin):
    """Регистрация команды /clear_tasks_list"""

    @bot.message_handler(commands=["clear_tasks_list"])
    def ask_clear_tasks(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к этой команде.")
            return

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="clear_tasks_confirm"),
            InlineKeyboardButton("❌ Нет", callback_data="clear_tasks_cancel")
        )

        bot.send_message(
            message.chat.id,
            "⚠ Вы действительно желаете очистить список ВЫПОЛНЕНЫХ задач?",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("clear_tasks_"))
    def handle_clear_confirmation(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Только для админов.")
            return

        if call.data == "clear_tasks_cancel":
            bot.edit_message_text(
                "🚫 Удаление отменено.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        elif call.data == "clear_tasks_confirm":
            clear_all_tasks()
            bot.edit_message_text(
                "✅ Информация удалена.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )

        bot.answer_callback_query(call.id)