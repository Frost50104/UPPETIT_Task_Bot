# ========= Перезапуск планировщика =========
import importlib
import schedule
import config
import auto_send_tasks_on_schedule
import datetime
from task_storage import assign_task

# === Перезапуск планировщика ===
def restart_scheduler(bot):
    importlib.reload(config)
    schedule.clear()

    # 🔁 Ежедневные задачи
    if config.status_work_time == "on":
        for time_str in config.work_time:
            schedule.every().day.at(time_str).do(auto_send_tasks_on_schedule.send_control_panel_tasks, bot)

    # 🔁 Еженедельные задачи
    if config.status_weekly == "on":
        for day, time_str in config.weekly_schedule:
            schedule_func = getattr(schedule.every(), day)
            schedule_func.at(time_str).do(send_weekly_tasks, bot)

    # 🔁 Ежемесячные задачи
    if config.status_monthly == "on":
        for day, time_str in config.monthly_schedule:
            # Каждый день в указанное время запускаем проверку
            schedule.every().day.at(time_str).do(check_and_send_monthly, bot, day)

    print(f"✅ Планировщик перезапущен!")
    print(f"📅 Ежедневно: {config.work_time if config.status_work_time == 'on' else '❌'}")
    print(f"🗓 Еженедельно: {config.weekly_schedule if config.status_weekly == 'on' else '❌'}")
    print(f"📆 Ежемесячно: {config.monthly_schedule if config.status_monthly == 'on' else '❌'}")

# === Еженедельные задачи по группам ===
def send_weekly_tasks(bot):
    for group_name, performers in config.performers_by_group.items():
        task_text = config.weekly_tasks.get(group_name)
        if not task_text:
            continue
        for user_id in performers:
            try:
                msg = bot.send_message(user_id, f"📌 <b>Еженедельная задача:</b>\n{task_text}", parse_mode="HTML")
                assign_task(user_id, task_text, msg.message_id)
            except Exception as e:
                print(f"⚠ Ошибка при отправке еженедельной задачи пользователю {user_id}: {e}")

# === Ежемесячные задачи (с проверкой дня) ===
def check_and_send_monthly(bot, target_day):
    today = datetime.datetime.now().day
    if today == target_day:
        send_monthly_tasks(bot)

def send_monthly_tasks(bot):
    for group_name, performers in config.performers_by_group.items():
        task_text = config.monthly_tasks.get(group_name)
        if not task_text:
            continue
        for user_id in performers:
            try:
                msg = bot.send_message(user_id, f"📌 <b>Ежемесячная задача:</b>\n{task_text}", parse_mode="HTML")
                assign_task(user_id, task_text, msg.message_id)
            except Exception as e:
                print(f"⚠ Ошибка при отправке ежемесячной задачи пользователю {user_id}: {e}")
