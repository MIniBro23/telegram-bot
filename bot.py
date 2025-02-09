import asyncio
import re
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

TOKEN = os.getenv("7654324736:AAHHU91BadBbPxSrkvI9Y9O-T1GmmfJgBnU")  # Получаем токен из переменной окружения

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# 📌 Хранение напоминаний
reminders = {}

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

@dp.message(lambda message: message.text == "➕ Добавить напоминание")
async def add_reminder_handler(message: types.Message):
    await message.answer("Напиши команду `/remind 30m Сделать зарядку` или `/remind 2h Позвонить другу`.")

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

    chat_id = message.chat.id
    reminder_id = len(reminders.get(chat_id, [])) + 1
    if chat_id not in reminders:
        reminders[chat_id] = []
    reminders[chat_id].append((reminder_id, remind_time, text))

    scheduler.add_job(send_reminder, "date", run_date=remind_time, args=[chat_id, reminder_id])

    await message.answer(f"✅ Напоминание #{reminder_id} установлено через {amount} {'минут' if unit == 'm' else 'часов'}.")

async def send_reminder(chat_id, reminder_id):
    """Отправляет напоминание и удаляет его из списка"""
    if chat_id in reminders:
        for reminder in reminders[chat_id]:
            if reminder[0] == reminder_id:
                await bot.send_message(chat_id, f"🔔 Напоминание: {reminder[2]}")
                reminders[chat_id].remove(reminder)
                break

@dp.message(lambda message: message.text == "📋 Мои напоминания")
async def list_reminders_handler(message: types.Message):
    """Показывает список активных напоминаний"""
    chat_id = message.chat.id
    if chat_id not in reminders or len(reminders[chat_id]) == 0:
        await message.answer("🔹 У тебя нет активных напоминаний.")
        return

    text = "📋 *Твои напоминания:*\n"
    for reminder in reminders[chat_id]:
        time_left = (reminder[1] - datetime.now()).total_seconds() // 60
        text += f"🔹 *#{reminder[0]}* – {reminder[2]} (осталось ~{int(time_left)} мин)\n"

    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("remove"))
async def remove_reminder_handler(message: types.Message):
    """Удаляет напоминание по ID"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Используй формат: `/remove <ID>`\n\nПример:\n`/remove 1`", parse_mode="Markdown")
        return

    reminder_id = int(args[1])
    chat_id = message.chat.id

    if chat_id in reminders:
        for reminder in reminders[chat_id]:
            if reminder[0] == reminder_id:
                reminders[chat_id].remove(reminder)
                await message.answer(f"✅ Напоминание #{reminder_id} удалено.")
                return

    await message.answer("⚠️ Напоминание с таким ID не найдено.")

async def main():
    scheduler.start()
    print("✅ Бот успешно запущен и работает!")  # Сообщение в консоли
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
