
import importlib
import config
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

def handle_cmnd_all_task(bot, is_admin, task_data):
    """Регистрация обработчиков команды /user_task"""

    # ========= Ручная постановка задачи (админом) =========
    @bot.message_handler(commands=['all_task'])
    def new_task(message):
        """Запрашивает у администратора текст задачи."""
        if not message.from_user.id in config.ADMIN_ID:
            bot.send_message(message.chat.id, "⛔ У вас нет прав ставить задачи.")
            return

        bot.send_message(message.chat.id, "✏ Введите текст задачи (или напишите 'отмена' для выхода):")
        bot.register_next_step_handler(message, send_task_to_performers, message.chat.id)

    def send_task_to_performers(message, admin_chat_id):
        """Обрабатывает введенный текст задачи, отменяет команду, если введено 'отмена'."""
        if message.text.lower() == "отмена":
            bot.send_message(admin_chat_id, "🚫 Создание задачи отменено.")
            return  # Завершаем обработчик

        task_text = message.text  # Получаем текст задания
        total_sent = 0  # Счетчик успешно отправленных сообщений

        for performers, tasks_text in config.control_panel.items():
            for performer in performers:
                try:
                    bot.send_message(performer, f"📌 *Новое задание:*\n{task_text}", parse_mode="Markdown")
                    bot.send_message(performer, "📷 Отправьте фото выполнения.")
                    task_data[performer] = {"task_text": task_text}
                    total_sent += 1  # Увеличиваем счетчик
                except telebot.apihelper.ApiTelegramException as e:
                    if "bot was blocked by the user" in str(e):
                        print(f"⚠ Бот заблокирован пользователем {performer}.")
                    else:
                        print(f"⚠ Ошибка при отправке задания пользователю {performer}: {e}")

        # ✅ Отправляем подтверждение администратору
        if total_sent > 0:
            bot.send_message(admin_chat_id, f"✅ Задача успешно отправлена {total_sent} сотрудникам!")
        else:
            bot.send_message(admin_chat_id, "⚠ Никому не удалось отправить задачу.")
