import os
import functools
import traceback
from datetime import datetime
from telebot.types import Message, CallbackQuery

# File to store all logs
ALL_LOGS_FILE = "all_logs.txt"

def log_action(user_id, action, details=None, user_cache=None, admin_name=None):
    """
    Log any bot action to the all_logs.txt file

    Args:
        user_id (int): ID of the user who performed the action
        action (str): Description of the action performed
        details (str, optional): Additional details about the action
        user_cache (dict or callable, optional): User cache to get user's name
        admin_name (str, optional): Name of the admin who performed the action
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get user's display name
    display_name = str(user_id)
    if user_cache:
        try:
            uid_str = str(user_id)
            uid_int = int(user_id)

            if callable(user_cache):
                user_data = user_cache(user_id)
            else:
                user_data = user_cache.get(uid_str) or user_cache.get(uid_int)

            if user_data:
                display_name = user_data.get("first_name") or user_data.get("username") or uid_str
        except Exception as e:
            print(f"⚠ Ошибка при получении данных пользователя из кэша: {e}")

    # Format details
    details_str = f" - {details}" if details else ""

    # Admin info
    admin_info = f" (админ: {admin_name})" if admin_name else ""

    # Create log line
    log_line = f"[{timestamp}] {display_name} - {action}{details_str}{admin_info}\n"

    # Write to log file
    with open(ALL_LOGS_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

def log_command(action_description):
    """
    Decorator to log command handlers

    Args:
        action_description (str): Description of the action being performed

    Returns:
        function: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(message, *args, **kwargs):
            # Check if message is a Message or CallbackQuery
            if isinstance(message, Message):
                user_id = message.from_user.id
                user_name = message.from_user.first_name
                command = message.text if hasattr(message, 'text') else "Неизвестная команда"
            elif isinstance(message, CallbackQuery):
                user_id = message.from_user.id
                user_name = message.from_user.first_name
                command = message.data if hasattr(message, 'data') else "Неизвестный callback"
            else:
                user_id = 0
                user_name = "Неизвестный пользователь"
                command = "Неизвестная команда"

            # Log the action
            log_action(
                user_id=user_id,
                action=action_description,
                details=f"Команда: {command}",
                admin_name=user_name
            )

            # Call the original function
            return func(message, *args, **kwargs)
        return wrapper
    return decorator

def get_all_logs():
    """
    Get all logs from the all_logs.txt file

    Returns:
        str: All logs or empty string if file doesn't exist
    """
    if not os.path.exists(ALL_LOGS_FILE):
        return ""

    with open(ALL_LOGS_FILE, "r", encoding="utf-8") as f:
        return f.read()

def clear_all_logs():
    """
    Clear all logs by removing the all_logs.txt file
    """
    if os.path.exists(ALL_LOGS_FILE):
        os.remove(ALL_LOGS_FILE)

def log_error(error, context=None):
    """
    Log an error to the all_logs.txt file

    Args:
        error (Exception): The error that occurred
        context (str, optional): Additional context about where the error occurred
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get error details
    error_type = type(error).__name__
    error_message = str(error)
    error_traceback = traceback.format_exc()

    # Format context
    context_str = f" в {context}" if context else ""

    # Create log line
    log_line = f"[{timestamp}] ОШИБКА{context_str} - Тип: {error_type}, Сообщение: {error_message}\n"
    log_line += f"Трассировка:\n{error_traceback}\n"

    # Write to log file
    with open(ALL_LOGS_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

def log_bot_restart():
    """
    Log a bot restart to the all_logs.txt file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create log line
    log_line = f"[{timestamp}] СИСТЕМА - Бот был перезапущен\n"

    # Write to log file
    with open(ALL_LOGS_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)
