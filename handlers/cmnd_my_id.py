# Обработчик команды /my_id
from telebot import types
from telebot.types import Message

def handle_cmnd_my_id(bot):
    @bot.message_handler(commands=['my_id'])
    def handle_command_my_id(message: types.Message):
        bot.send_message(
            message.chat.id,
            f'ID пользователя <b>{message.from_user.first_name}</b> ({message.from_user.username}):\n<pre>{message.from_user.id}</pre>',
            parse_mode="HTML"
        )