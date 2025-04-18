import inspect
import functools
from logger import log_command

def decorate_handler(handler_func, command_name=None):
    """
    Decorates a handler function with the log_command decorator.

    Args:
        handler_func (function): The handler function to decorate
        command_name (str, optional): The name of the command. If not provided,
                                     it will be extracted from the function name.

    Returns:
        function: The decorated handler function
    """
    # Extract command name from function name if not provided
    if not command_name:
        func_name = handler_func.__name__
        if func_name.startswith('handle_'):
            command_name = func_name[7:]  # Remove 'handle_' prefix
        elif func_name.startswith('handle_cmnd_'):
            command_name = func_name[12:]  # Remove 'handle_cmnd_' prefix
        elif func_name.startswith('handle_command_'):
            command_name = func_name[15:]  # Remove 'handle_command_' prefix
        else:
            command_name = func_name

    # Create a description for the log
    action_description = f"Выполнил команду /{command_name}"

    def wrapper(*args, **kwargs):
        # The first argument is typically the bot instance
        bot = args[0]
        original_message_handler = bot.message_handler
        original_callback_query_handler = bot.callback_query_handler
        original_register_next_step_handler = bot.register_next_step_handler
        original_register_next_step_handler_by_chat_id = getattr(bot, 'register_next_step_handler_by_chat_id', None)

        # Override the bot.message_handler method to apply our decorator
        def decorated_message_handler(*dargs, **dkwargs):
            original_decorator = original_message_handler(*dargs, **dkwargs)

            def wrapper_decorator(handler_function):
                # Apply the log_command decorator to the inner handler function
                decorated_handler = log_command(action_description)(handler_function)
                return original_decorator(decorated_handler)

            return wrapper_decorator

        # Override the bot.callback_query_handler method to apply our decorator
        def decorated_callback_query_handler(*dargs, **dkwargs):
            original_decorator = original_callback_query_handler(*dargs, **dkwargs)

            def wrapper_decorator(handler_function):
                # Apply the log_command decorator to the inner handler function
                decorated_handler = log_command(action_description)(handler_function)
                return original_decorator(decorated_handler)

            return wrapper_decorator

        # Override the register_next_step_handler method to apply our decorator
        def decorated_register_next_step_handler(message, callback, *args, **kwargs):
            # Apply the log_command decorator to the callback function
            decorated_callback = log_command(f"Следующий шаг для команды /{command_name}")(callback)
            return original_register_next_step_handler(message, decorated_callback, *args, **kwargs)

        # Override the register_next_step_handler_by_chat_id method if it exists
        def decorated_register_next_step_handler_by_chat_id(chat_id, callback, *args, **kwargs):
            if original_register_next_step_handler_by_chat_id:
                # Apply the log_command decorator to the callback function
                decorated_callback = log_command(f"Следующий шаг для команды /{command_name}")(callback)
                return original_register_next_step_handler_by_chat_id(chat_id, decorated_callback, *args, **kwargs)
            return None

        # Replace the bot methods temporarily
        bot.message_handler = decorated_message_handler
        bot.callback_query_handler = decorated_callback_query_handler
        bot.register_next_step_handler = decorated_register_next_step_handler
        if original_register_next_step_handler_by_chat_id:
            bot.register_next_step_handler_by_chat_id = decorated_register_next_step_handler_by_chat_id

        # Call the original handler function
        result = handler_func(*args, **kwargs)

        # Restore the original bot methods
        bot.message_handler = original_message_handler
        bot.callback_query_handler = original_callback_query_handler
        bot.register_next_step_handler = original_register_next_step_handler
        if original_register_next_step_handler_by_chat_id:
            bot.register_next_step_handler_by_chat_id = original_register_next_step_handler_by_chat_id

        return result

    # Preserve the original function's attributes
    functools.update_wrapper(wrapper, handler_func)

    return wrapper
