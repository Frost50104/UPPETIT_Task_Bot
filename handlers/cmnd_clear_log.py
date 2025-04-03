import os
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

LOG_FILE = "task_log.txt"

def handle_cmnd_clear_log(bot, is_admin):
    @bot.message_handler(commands=["clear_log"])
    def ask_clear_log(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к этой команде.", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="clear_log_confirm"),
            InlineKeyboardButton("❌ Нет", callback_data="clear_log_cancel")
        )

        bot.send_message(
            message.chat.id,
            "🗑 <b>Удалить логи?</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("clear_log_"))
    def process_log_clear(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Только для админов.")
            return

        if call.data == "clear_log_cancel":
            bot.edit_message_text(
                "❌ Удаление логов отменено.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        elif call.data == "clear_log_confirm":
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            bot.edit_message_text(
                "✅ Логи успешно удалены!",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )

        bot.answer_callback_query(call.id)