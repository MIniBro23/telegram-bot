import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ВСТАВЬТЕ СВОЙ API-ТОКЕН СЮДА
TOKEN = "7654324736:AAHHU91BadBbPxSrkvI9Y9O-T1GmmfJgBnU"

# Проверяем, что токен не пустой
if not TOKEN:
    raise ValueError("Ошибка: Токен бота не найден! Вставьте свой API-токен в переменную TOKEN.")

# Настраиваем логирование (полезно для отладки)
logging.basicConfig(level=logging.INFO)

# Создаем объект бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Команда /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Привет! Я твой бот 🤖\n\nОтправь мне любое сообщение, и я повторю его!")

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
