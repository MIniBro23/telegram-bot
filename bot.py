import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

TOKEN = "7654324736:AAHHU91BadBbPxSrkvI9Y9O-T1GmmfJgBnU"  # Замени на свой токен

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# 📌 Клавиатура с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить напоминание")],
        [KeyboardButton(text="📋 Мои напоминания")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка. Используй /remind <время> <текст>.\n\nПример:\n/remind 30m Сделать зарядку\n/remind 2h Пойти на встречу", reply_markup=main_keyboard)

# ✅ Обработчик кнопки "➕ Добавить напоминание"
@dp.message(lambda message: message.text == "➕ Добавить напоминание")
async def add_reminder_handler(message: types.Message):
    await message.answer("Напиши команду `/remind 30m Сделать зарядку` или `/remind 2h Позвонить другу`.")

# ✅ Обработчик кнопки "📋 Мои напоминания" (можно доработать)
@dp.message(lambda message: message.text == "📋 Мои напоминания")
async def list_reminders_handler(message: types.Message):
    await message.answer("Пока я не храню список напоминаний, но скоро добавлю этот функционал! 😉")

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
