from task_storage import load_tasks
from users_cache import get_user_from_cache

def handle_cmnd_tasks_list(bot, is_admin):
    @bot.message_handler(commands=["tasks_list"])
    def show_tasks_list(message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа к этой команде.", parse_mode="HTML")
            return

        tasks = load_tasks()
        if not tasks:
            bot.reply_to(message, "📭 Нет активных задач.", parse_mode="HTML")
            return

        grouped_tasks = {}

        for uid, task_list in tasks.items():
            for task in task_list:
                key = (task["task_text"], task["assigned_at"].split("T")[0])
                if key not in grouped_tasks:
                    grouped_tasks[key] = []
                grouped_tasks[key].append({
                    "user_id": uid,
                    "status": task["status"],
                    "reminder": bool(task.get("reminder_message_id"))
                })

        MAX_LEN = 4000
        message_block = ""

        for (task_text, date), users in grouped_tasks.items():
            block = f"📋 <b>{task_text}</b>\n📅 <i>{date}</i>\n<b>Исполнители:</b>\n"
            for user in users:
                uid = user["user_id"]
                user_data = get_user_from_cache(uid) or {}
                name = user_data.get("first_name") or user_data.get("username") or f"ID: {uid}"
                status = user["status"]
                reminder_flag = " ⏰" if user["reminder"] else ""
                block += f"👤 {name} ({uid}) — {status}{reminder_flag}\n"

            if len(message_block) + len(block) > MAX_LEN:
                bot.send_message(message.chat.id, message_block, parse_mode="HTML")
                message_block = ""
            message_block += "\n" + block

        if message_block:
            bot.send_message(message.chat.id, message_block, parse_mode="HTML")