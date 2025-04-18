# Обработчик команды /help
from telebot import types
from telebot.types import Message
import help_message

def handle_cmnd_help(bot, is_admin):
    @bot.message_handler(commands=['help'])
    def handle_command_help(message: types.Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к справочной информации.", parse_mode="HTML")
            return
        bot.send_message(message.chat.id, help_message.help_msg, parse_mode="HTML")