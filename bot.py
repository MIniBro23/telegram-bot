import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

TOKEN = "7654324736:AAFQ4s1TxADfqYCZ2FvB0zcdn3wyvDnPrLM"  # Замени на свой токен

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

reminders = {}  # Словарь для хранения напоминаний

# 📌 Клавиатура с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить напоминание")],
        [KeyboardButton(text="📋 Мои напоминания")]
    ],
    resize_keyboard=True
)

# ⏳ Кнопки для быстрого выбора времени напоминания
time_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="5 минут", callback_data="remind_5"),
         InlineKeyboardButton(text="10 минут", callback_data="remind_10"),
         InlineKeyboardButton(text="15 минут", callback_data="remind_15")]
    ]
)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка. Выбери действие:", reply_markup=main_keyboard)

@dp.message(lambda message: message.text == "➕ Добавить напоминание")
async def add_reminder_handler(message: types.Message):
    await message.answer("Выбери время напоминания:", reply_markup=time_keyboard)

@dp.callback_query(lambda call: call.data.startswith("remind_"))
async def inline_reminder_handler(callback: types.CallbackQuery):
    delay = int(callback.data.split("_")[1])
    text = "Напоминание!"  # Можно улучшить, чтобы пользователь вводил текст
    remind_time = datetime.now() + timedelta(minutes=delay)

    # Создание задачи напоминания
    scheduler.add_job(send_reminder, "date", run_date=remind_time, args=[callback.message.chat.id, text])

    await callback.message.answer(f"✅ Напоминание установлено через {delay} минут.")
    await callback.answer()

async def send_reminder(chat_id, text):
    await bot.send_message(chat_id, f"🔔 Напоминание: {text}")

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
