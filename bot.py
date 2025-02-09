import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен из переменных окружения
TOKEN = os.getenv("TOKEN")

# Проверяем, что токен загружен
if not TOKEN:
    raise ValueError("Ошибка: Токен бота не найден! Проверьте переменные окружения или .env файл.")

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Команда /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Привет! Я твой бот 🤖")

# Команда /help
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.reply("Доступные команды:\n/start - Запустить бота\n/help - Получить справку")

# Эхо-ответ на любые сообщения
@dp.message_handler()
async def echo_message(message: types.Message):
    await message.reply(f"Ты сказал: {message.text}")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
