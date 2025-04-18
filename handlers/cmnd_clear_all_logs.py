import os
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from logger import clear_all_logs, log_action

def handle_cmnd_clear_all_logs(bot, is_admin):
    @bot.message_handler(commands=["clear_all_logs"])
    def ask_clear_all_logs(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к этой команде.", parse_mode="HTML")
            return
            
        # Log the action
        log_action(
            user_id=message.from_user.id,
            action="Запросил очистку всех логов",
            details="Команда /clear_all_logs",
            admin_name=message.from_user.first_name
        )

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data="clear_all_logs_confirm"),
            InlineKeyboardButton("❌ Нет", callback_data="clear_all_logs_cancel")
        )

        bot.send_message(
            message.chat.id,
            "🗑 <b>Удалить все логи?</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("clear_all_logs_"))
    def process_all_logs_clear(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Только для админов.")
            return

        if call.data == "clear_all_logs_cancel":
            bot.edit_message_text(
                "❌ Удаление всех логов отменено.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
            
            # Log the action
            log_action(
                user_id=call.from_user.id,
                action="Отменил очистку всех логов",
                admin_name=call.from_user.first_name
            )
            
        elif call.data == "clear_all_logs_confirm":
            clear_all_logs()
            
            bot.edit_message_text(
                "✅ Все логи успешно удалены!",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
            
            # Log the action (this will be the first entry in the new log file)
            log_action(
                user_id=call.from_user.id,
                action="Очистил все логи",
                admin_name=call.from_user.first_name
            )

        bot.answer_callback_query(call.id)