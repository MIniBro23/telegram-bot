import asyncio
import logging
from aiogram import Bot, Dispatcher, types

# ВСТАВЬТЕ СВОЙ API-ТОКЕН
TOKEN = "7654324736:AAHHU91BadBbPxSrkvI9Y9O-T1GmmfJgBnU"

# Проверяем, что токен введён
if not TOKEN:
    raise ValueError("Ошибка: Токен бота не найден!")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Создаём объект бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("Привет! Я твой бот 🤖")

# Обработчик команды /help
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.answer("Доступные команды:\n/start - Запустить бота\n/help - Получить справку")

# Эхо-бот (повторяет сообщения)
@dp.message_handler()
async def echo_message(message: types.Message):
    await message.answer(f"Ты сказал: {message.text}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
