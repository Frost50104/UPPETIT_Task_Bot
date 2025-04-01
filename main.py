# from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# from telebot import types
# import help_message
# import schedule
# import calendar
# import datetime
# import time
# import threading
# import ast
# import re
# import hashlib
# import importlib
# import json
# from users_cache import build_user_cache
# import auto_send_tasks_on_schedule
# import restart_scheduler
import telebot
import config  # Файл с переменными
from bot_instance import bot, is_admin, task_data
from restart_scheduler import restart_scheduler
from scheduler_thread import start_scheduler_thread
from handlers.cmnd_start import handle_cmnd_start
from handlers.cmnd_admins import handle_cmnd_admins
from handlers.cmnd_help import handle_cmnd_help
from handlers.cmnd_my_id import handle_cmnd_my_id
from handlers.cmnd_chat_id import handle_cmnd_chat_id
from handlers.cmnd_set_group_name import handle_cmnd_set_group_name
from handlers.cmnd_add_user import handle_cmnd_add_user
from handlers.cmnd_delete_user import handle_cmnd_delete_user
from handlers.cmnd_set_task_group import handle_cmnd_set_task_group
from handlers.cmnd_group_task import handle_cmnd_group_task
from handlers.cmnd_user_task import handle_cmnd_user_task
from handlers.cmnd_delete_admin import handle_cmnd_delete_admin
from handlers.cmnd_add_admin import handle_cmnd_add_admin
from handlers.cmnd_auto_send import handle_cmnd_auto_send
from handlers.cmnd_set_time import handle_cmnd_set_time
from handlers.cmnd_set_month import handle_cmnd_set_month
from handlers.cmnd_auto_send_monthly import handle_cmnd_auto_send_monthly
from handlers.cmnd_set_day import handle_cmnd_set_day
from handlers.cmnd_auto_send_weekly import handle_cmnd_auto_send_weekly
from handlers.cmnd_update_user_cache import handle_cmnd_update_user_cache
from handlers.cmnd_bot_users import handle_cmnd_bot_users
from handlers.cmnd_all_task import handle_cmnd_all_task
from handlers.cmnd_show_schedule import handle_cmnd_show_schedule
from handlers.photo_submission import handle_photo_submission

from config import ADMIN_ID

# Создание бота
bot = telebot.TeleBot(config.TOKEN)
# переключить бота с тестового на основного

# ========= Функция экранирования MarkdownV2 =========
def escape_markdown_v2(text):
    """Экранирует специальные символы для MarkdownV2"""
    special_chars = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in special_chars else char for char in text)

# ========= Скрипты =========
restart_scheduler(bot) # перезапуск планировщика
start_scheduler_thread() # фоновый процесс планировщика

# ========= Стандартные команды =========
handle_cmnd_start(bot) # команда /start
handle_cmnd_admins(bot) # команда /admins
handle_cmnd_help(bot) # команда /help
handle_cmnd_my_id(bot) # команда /my_id
handle_cmnd_chat_id(bot) # команда /chat_id
handle_cmnd_set_group_name(bot, is_admin) # команда /set_group_name
handle_cmnd_add_user(bot, is_admin, task_data) # команда /add_user
handle_cmnd_delete_user(bot, is_admin, task_data) # команда /delete_user
handle_cmnd_set_task_group(bot, is_admin, task_data, config.daily_tasks, config.weekly_tasks, config.monthly_tasks) # команда /set_task_group
handle_cmnd_group_task(bot, is_admin, task_data) # команда /group_task
handle_cmnd_user_task(bot, is_admin, task_data) # команда /user_task
handle_cmnd_add_admin(bot, is_admin, task_data) # команда /add_admin
handle_cmnd_delete_admin(bot, is_admin) # команда /delete_admin
handle_cmnd_auto_send_monthly(bot, is_admin, lambda: restart_scheduler(bot)) # команда /auto_send_monthly
handle_cmnd_update_user_cache(bot, is_admin) # обновление кэша списка пользователей для bot_users
handle_cmnd_bot_users(bot, is_admin) # команда /bot_users
handle_cmnd_all_task(bot, is_admin, task_data) # команда /all_task
handle_cmnd_show_schedule(bot, is_admin) # команда /show_schedule
handle_photo_submission(bot, task_data) # работа с фото в контрольном чате
handle_cmnd_auto_send(bot, is_admin, lambda: restart_scheduler(bot)) # команда /auto_send
handle_cmnd_set_time(bot, is_admin, lambda: restart_scheduler(bot)) # команда /set_time
handle_cmnd_set_month(bot, is_admin, lambda: restart_scheduler(bot)) # команда /set_month
handle_cmnd_set_day(bot, is_admin, lambda: restart_scheduler(bot)) # команда /set_day
handle_cmnd_auto_send_weekly(bot, is_admin, lambda: restart_scheduler(bot)) # команда /auto_send_weekly


# ========= Запуск бота =========
if __name__ == "__main__":
    print("✅ Бот запущен!")
    bot.polling(none_stop=True)