from telebot import types
import config

# ========= Показать статус рассылок =========
DAYS_RU = {
    'monday': 'Понедельник',
    'tuesday': 'Вторник',
    'wednesday': 'Среда',
    'thursday': 'Четверг',
    'friday': 'Пятница',
    'saturday': 'Суббота',
    'sunday': 'Воскресенье'
}

def translate_weekly_schedule(weekly_schedule):
    # Пример: [('monday', '10:00'), ('friday', '15:30')]
    result = []
    for day, time in weekly_schedule:
        day_ru = DAYS_RU.get(day.lower(), day)
        result.append(f"{day_ru} в {time}")
    return '\n'.join(result) if result else '—'

def translate_monthly_schedule(monthly_schedule):
    # Пример: [(1, '10:00'), (15, '12:00')]
    result = []
    for day, time in sorted(monthly_schedule, key=lambda x: int(x[0])):
        result.append(f"{day} числа в {time}")
    return '\n'.join(result) if result else '—'

def format_tasks_and_groups(tasks_dict):
    """Форматирует словарь задач и групп получателей"""
    if not tasks_dict:
        return "Нет задач"

    # Получаем уникальные задачи
    unique_tasks = set(tasks_dict.values())

    # Если задач нет, возвращаем сообщение
    if not unique_tasks:
        return "Нет задач"

    # Если задача одна для всех групп, выводим её один раз
    if len(unique_tasks) == 1:
        task_text = next(iter(unique_tasks))

        # Формируем список групп получателей
        groups_info = []
        for group_name in tasks_dict.keys():
            # Получаем название группы в читаемом формате
            readable_group_name = group_name.replace("task_group_", "Группа ")

            # Получаем список ID получателей для этой группы
            recipients = config.performers_by_group.get(group_name, [])

            # Находим название группы из словаря performers
            group_display_name = None
            for name, ids in config.performers.items():
                if set(ids) == set(recipients):
                    group_display_name = name
                    break

            group_info = group_display_name or readable_group_name
            groups_info.append(f"• <b>{group_info}</b> ({len(recipients)} получателей)")

        # Формируем результат: сначала задача, потом список групп
        result = f"<b>Задача:</b> {task_text}\n\n<b>Группы получателей:</b>\n" + '\n'.join(groups_info)
        return result

    # Если задачи разные для разных групп (что не должно быть по условию задачи),
    # используем старый формат вывода
    result = []
    for group_name, task_text in tasks_dict.items():
        # Получаем название группы в читаемом формате
        readable_group_name = group_name.replace("task_group_", "Группа ")

        # Получаем список ID получателей для этой группы
        recipients = config.performers_by_group.get(group_name, [])

        # Находим название группы из словаря performers
        group_display_name = None
        for name, ids in config.performers.items():
            if set(ids) == set(recipients):
                group_display_name = name
                break

        group_info = group_display_name or readable_group_name
        result.append(f"• <b>{group_info}</b>: {task_text} ({len(recipients)} получателей)")

    return '\n'.join(result) if result else "Нет задач"

def handle_cmnd_show_schedule(bot, is_admin):
    """Регистрация обработчика команды /show_schedule"""
    @bot.message_handler(commands=['show_schedule'])
    def handle_command_show_schedule(message: types.Message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав смотреть статус автоматической рассылки.")
            return

        weekly_text = translate_weekly_schedule(config.weekly_schedule)
        monthly_text = translate_monthly_schedule(config.monthly_schedule)

        # Форматируем задачи и группы получателей
        daily_tasks_text = format_tasks_and_groups(config.daily_tasks)
        weekly_tasks_text = format_tasks_and_groups(config.weekly_tasks)
        monthly_tasks_text = format_tasks_and_groups(config.monthly_tasks)

        bot.send_message(
            message.chat.id,
            text=f'''
🗓 <b>Ежедневная рассылка:</b> {config.status_work_time}
Время: {', '.join(config.work_time) if config.work_time else '—'}\n
{daily_tasks_text}

📆 <b>Еженедельная рассылка:</b> {config.status_weekly}
Дни и время: {weekly_text}\n
{weekly_tasks_text}

📅 <b>Ежемесячная рассылка:</b> {config.status_monthly}
Даты и время: {monthly_text}\n
{monthly_tasks_text}
''',
            parse_mode='HTML'
        )
