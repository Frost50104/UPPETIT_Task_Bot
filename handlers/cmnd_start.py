# Обработчик команды /start
from telebot import types
from telebot.types import Message

def handle_cmnd_start(bot):
    @bot.message_handler(commands=['start'])
    def handle_command_start(message: types.Message):
        bot.send_message(message.chat.id, "Привет! Я бот для постановки задач")
        bot.send_message(
            message.chat.id,
            f'ID пользователя <b>{message.from_user.first_name}</b> ({message.from_user.username}):\n<pre>{message.from_user.id}</pre>',
            parse_mode="HTML"
        )