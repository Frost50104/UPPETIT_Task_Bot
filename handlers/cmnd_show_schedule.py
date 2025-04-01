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

def handle_cmnd_show_schedule(bot, is_admin):
    """Регистрация обработчика команды /show_schedule"""
    @bot.message_handler(commands=['show_schedule'])
    def handle_command_show_schedule(message: types.Message):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав смотреть статус автоматической рассылки.")
            return

        weekly_text = translate_weekly_schedule(config.weekly_schedule)
        monthly_text = translate_monthly_schedule(config.monthly_schedule)

        bot.send_message(
            message.chat.id,
            text=f'''
🗓 <b>Ежедневная рассылка:</b> {config.status_work_time}
Время: {', '.join(config.work_time) if config.work_time else '—'}
    
📆 <b>Еженедельная рассылка:</b> {config.status_weekly}
Дни и время: {weekly_text}
    
📅 <b>Ежемесячная рассылка:</b> {config.status_monthly}
Даты и время: {monthly_text}
''',
            parse_mode='HTML'
        )