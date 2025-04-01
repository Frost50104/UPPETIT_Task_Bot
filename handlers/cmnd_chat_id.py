# Обработчик команды /chat_id
from telebot import types
from telebot.types import Message

def handle_cmnd_chat_id(bot):
    @bot.message_handler(commands=['chat_id'])
    def handle_command_chat_id(message: types.Message):
        bot.send_message(
            message.chat.id,
            f'ID чата:\n<pre>{message.chat.id}</pre>',
            parse_mode="HTML"
        )