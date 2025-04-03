# Обработчик команды /help
from telebot import types
from telebot.types import Message
import help_message

def handle_cmnd_help(bot):
    @bot.message_handler(commands=['help'])
    def handle_command_help(message: types.Message):
        bot.send_message(message.chat.id, help_message.help_msg, parse_mode="HTML")