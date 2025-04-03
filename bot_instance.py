from telebot import TeleBot
import config


# Создание экземпляра бота
bot = TeleBot(config.TOKEN)

# Словарь для хранения временных данных по пользователям (например, для /add_user)
task_data = {}

# ========= Проверка прав администратора =========
def is_admin(user_id):
    """Проверяет, является ли пользователь администратором."""
    return user_id in config.ADMIN_ID
