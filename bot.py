import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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

@dp.message(Command("remind"))
async def remind_handler(message: types.Message):
    args = message.text.split(maxsplit=2)
    
    if len(args) < 3:
        await message.answer("⚠️ Используй формат: /remind <время> <текст>\n\nПример:\n/remind 30m Сделать зарядку\n/remind 2h Пойти на встречу")
        return

    time_str, text = args[1], args[2]

    # Парсим время (форматы: "30m", "2h")
    match = re.match(r"(\d+)([mh])", time_str)
    if not match:
        await message.answer("⚠️ Неверный формат времени! Используй:\n- `Xm` (минуты)\n- `Xh` (часы)\n\nПример:\n/remind 45m Пауза\n/remind 3h Встреча", parse_mode="Markdown")
        return

    amount, unit = int(match.group(1)), match.group(2)
    delay = amount * 60 if unit == "m" else amount * 3600  # Минуты или часы в секундах

    remind_time = datetime.now() + timedelta(seconds=delay)

    # Создаём задачу напоминания
    scheduler.add_job(send_reminder, "date", run_date=remind_time, args=[message.chat.id, text])

    await message.answer(f"✅ Напоминание установлено через {amount} {'минут' if unit == 'm' else 'часов'}.")

async def send_reminder(chat_id, text):
    await bot.send_message(chat_id, f"🔔 Напоминание: {text}")

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
