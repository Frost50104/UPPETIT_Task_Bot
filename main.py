import json
import telebot
import config  # Файл с переменными
from bot_instance import bot, is_admin, task_data
from restart_scheduler import restart_scheduler
from scheduler_thread import start_scheduler_thread
from handlers.handler_decorator import decorate_handler
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
from handlers.cmnd_tasks_list import handle_cmnd_tasks_list
from handlers.cmnd_clear_tasks_list import handle_cmnd_clear_tasks_list
from handlers.cmnd_clear_all_tasks_list import handle_cmnd_clear_all_tasks_list
from handlers.cmnd_arbeiten import handle_cmnd_arbeiten
from handlers.cmnd_show_log import handle_cmnd_show_log
from handlers.cmnd_clear_log import handle_cmnd_clear_log
from handlers.cmnd_all_logs import handle_cmnd_all_logs
from handlers.cmnd_clear_all_logs import handle_cmnd_clear_all_logs
from handlers.cmnd_planning import handle_cmnd_planning
from users_cache import build_user_cache
from logger import log_action, log_error, log_bot_restart





# Создание бота
bot = telebot.TeleBot(config.TOKEN)

# ========= Функция экранирования MarkdownV2 =========
def escape_markdown_v2(text):
    """Экранирует специальные символы для MarkdownV2"""
    special_chars = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in special_chars else char for char in text)

# ========= Скрипты =========
build_user_cache()  # Загружаем кэш в память
restart_scheduler(bot) # перезапуск планировщика
start_scheduler_thread() # фоновый процесс планировщика

# ========= Стандартные команды =========
decorate_handler(handle_cmnd_start, "start")(bot) # команда /start
decorate_handler(handle_cmnd_admins, "admins")(bot) # команда /admins
decorate_handler(handle_cmnd_help, "help")(bot, is_admin) # команда /help
decorate_handler(handle_cmnd_my_id, "my_id")(bot) # команда /my_id
decorate_handler(handle_cmnd_chat_id, "chat_id")(bot) # команда /chat_id
decorate_handler(handle_cmnd_set_group_name, "set_group_name")(bot, is_admin) # команда /set_group_name
decorate_handler(handle_cmnd_add_user, "add_user")(bot, is_admin, task_data) # команда /add_user
decorate_handler(handle_cmnd_delete_user, "delete_user")(bot, is_admin, task_data) # команда /delete_user
decorate_handler(handle_cmnd_set_task_group, "set_task_group")(bot, is_admin, task_data, config.daily_tasks, config.weekly_tasks, config.monthly_tasks) # команда /set_task_group
decorate_handler(handle_cmnd_group_task, "group_task")(bot, is_admin, task_data) # команда /group_task
decorate_handler(handle_cmnd_user_task, "user_task")(bot, is_admin, task_data) # команда /user_task
decorate_handler(handle_cmnd_add_admin, "add_admin")(bot, is_admin, task_data) # команда /add_admin
decorate_handler(handle_cmnd_delete_admin, "delete_admin")(bot, is_admin) # команда /delete_admin
decorate_handler(handle_cmnd_auto_send_monthly, "auto_send_monthly")(bot, is_admin, lambda: restart_scheduler(bot)) # команда /auto_send_monthly
decorate_handler(handle_cmnd_update_user_cache, "update_user_cache")(bot, is_admin) # обновление кэша списка пользователей для bot_users
decorate_handler(handle_cmnd_bot_users, "bot_users")(bot, is_admin) # команда /bot_users
decorate_handler(handle_cmnd_all_task, "all_task")(bot, is_admin, task_data) # команда /all_task
decorate_handler(handle_cmnd_show_schedule, "show_schedule")(bot, is_admin) # команда /show_schedule
decorate_handler(handle_photo_submission, "photo_submission")(bot) # работа с фото в контрольном чате
decorate_handler(handle_cmnd_auto_send, "auto_send")(bot, is_admin, lambda: restart_scheduler(bot)) # команда /auto_send
decorate_handler(handle_cmnd_set_time, "set_time")(bot, is_admin, lambda: restart_scheduler(bot)) # команда /set_time
decorate_handler(handle_cmnd_set_month, "set_month")(bot, is_admin, lambda: restart_scheduler(bot)) # команда /set_month
decorate_handler(handle_cmnd_set_day, "set_day")(bot, is_admin, lambda: restart_scheduler(bot)) # команда /set_day
decorate_handler(handle_cmnd_auto_send_weekly, "auto_send_weekly")(bot, is_admin, lambda: restart_scheduler(bot)) # команда /auto_send_weekly
decorate_handler(handle_cmnd_tasks_list, "tasks_list")(bot, is_admin)
decorate_handler(handle_cmnd_clear_tasks_list, "clear_tasks_list")(bot, is_admin)
decorate_handler(handle_cmnd_clear_all_tasks_list, "clear_all_tasks_list")(bot, is_admin)
decorate_handler(handle_cmnd_arbeiten, "arbeiten")(bot, is_admin)
decorate_handler(handle_cmnd_show_log, "show_log")(bot, is_admin)
decorate_handler(handle_cmnd_clear_log, "clear_log")(bot, is_admin)
decorate_handler(handle_cmnd_all_logs, "all_logs")(bot, is_admin)
decorate_handler(handle_cmnd_clear_all_logs, "clear_all_logs")(bot, is_admin)
decorate_handler(handle_cmnd_planning, "planning")(bot, is_admin, task_data)


# ========= Запуск бота =========
if __name__ == "__main__":
    print("✅ Бот запущен!")
    # Логируем перезапуск бота
    log_bot_restart()

    try:
        # Запускаем бота с обработкой ошибок
        bot.polling(none_stop=True)
    except Exception as e:
        # Логируем ошибку
        log_error(e, "при работе бота")
        print(f"❌ Ошибка при работе бота: {e}")
        # Пробуем перезапустить бота
        try:
            log_bot_restart()
            bot.polling(none_stop=True)
        except Exception as restart_error:
            log_error(restart_error, "при попытке перезапуска бота")
            print(f"❌ Не удалось перезапустить бота: {restart_error}")
