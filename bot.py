import asyncio
import os
import re
import pytz
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ✅ Часовой пояс Киев
KYIV_TZ = pytz.timezone("Europe/Kiev")

# ✅ Токен бота
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ Ошибка: TOKEN не найден!")

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# 📌 Хранение напоминаний
reminders = {}
user_states = {}  # Состояние пользователя

# 📌 Главное меню с кнопками
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить напоминание", callback_data="add_reminder")],
        [InlineKeyboardButton(text="📜 Мои напоминания", callback_data="list_reminders")]
    ])

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Приветственное сообщение с кнопками"""
    await message.answer("Привет! Я бот-напоминалка. 🕒\n\n"
                         "📌 Используй кнопки ниже для управления напоминаниями.", 
                         reply_markup=main_menu())

@dp.callback_query(lambda c: c.data == "add_reminder")
async def select_reminder_type(callback_query: types.CallbackQuery):
    """Выбор типа напоминания (через время или на дату)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Через время (30m, 2h)", callback_data="remind_time")],
        [InlineKeyboardButton(text="📅 На дату (10.02 13:13)", callback_data="remind_date")]
    ])
    await callback_query.message.edit_text("Выбери, как установить напоминание:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "remind_time")
async def ask_time_format(callback_query: types.CallbackQuery):
    """Просим ввести время в формате 30m, 2h"""
    user_states[callback_query.from_user.id] = "waiting_time"
    await callback_query.message.edit_text("Введите время в формате `30m`, `2h` и текст.\n\n"
                                           "Пример: `30m Перекусить 🍏`", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "remind_date")
async def ask_date_format(callback_query: types.CallbackQuery):
    """Просим ввести дату в формате 10.02 13:13"""
    user_states[callback_query.from_user.id] = "waiting_date"
    await callback_query.message.edit_text("Введите дату в формате `дд.мм чч:мм` и текст.\n\n"
                                           "Пример: `10.02 13:13 Позвонить другу`", parse_mode="Markdown")

@dp.message()
async def process_user_input(message: types.Message):
    """Обрабатываем ввод пользователя после выбора способа напоминания"""
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    user_state = user_states[user_id]
    del user_states[user_id]  # Удаляем состояние после обработки

    if user_state == "waiting_time":
        await process_time_reminder(message)
    elif user_state == "waiting_date":
        await process_date_reminder(message)

async def process_time_reminder(message: types.Message):
    """Установка напоминания через N минут/часов"""
    args = message.text.strip().split(None, 1)

    if len(args) < 2:
        await message.answer("⚠️ Формат: `30m ТЕКСТ` или `2h ТЕКСТ`")
        return

    time_str = args[0].strip()
    text = args[1].strip()
    match_relative = re.match(r"^(\d+)([mh])$", time_str)

    if match_relative:
        amount, unit = int(match_relative.group(1)), match_relative.group(2)
        delay = amount * 60 if unit == "m" else amount * 3600
        remind_time = datetime.now(KYIV_TZ) + timedelta(seconds=delay)
    else:
        await message.answer("❌ Ошибка: неверный формат времени!\nИспользуй `30m` или `2h`.", parse_mode="Markdown")
        return

    await set_reminder(message, remind_time, text)

async def process_date_reminder(message: types.Message):
    """Установка напоминания на конкретную дату"""
    args = message.text.strip().split(None, 2)

    if len(args) < 3:
        await message.answer("⚠️ Формат: `дд.мм чч:мм ТЕКСТ`")
        return

    time_str = f"{args[0]} {args[1]}"
    text = args[2].strip()
    match_absolute = re.match(r"^(\d{2})\.(\d{2}) (\d{2}):(\d{2})$", time_str)

    if match_absolute:
        try:
            day, month, hour, minute = map(int, match_absolute.groups())
            now = datetime.now(KYIV_TZ)
            year = now.year
            remind_time = KYIV_TZ.localize(datetime(year, month, day, hour, minute))
        except ValueError:
            await message.answer("❌ Ошибка: Некорректная дата или время.")
            return

        if remind_time < now:
            await message.answer("⚠️ Ошибка: Нельзя установить напоминание в прошлом!")
            return
    else:
        await message.answer("❌ Ошибка: неверный формат даты!\nИспользуй `дд.мм чч:мм`.", parse_mode="Markdown")
        return

    await set_reminder(message, remind_time, text)

async def set_reminder(message: types.Message, remind_time: datetime, text: str):
    """Общий метод для установки напоминания"""
    chat_id = message.chat.id
    reminder_id = len(reminders.get(chat_id, [])) + 1
    if chat_id not in reminders:
        reminders[chat_id] = []
    reminders[chat_id].append((reminder_id, remind_time, text))

    scheduler.add_job(send_reminder, "date", run_date=remind_time, args=[chat_id, reminder_id])

    await message.answer(f"✅ Напоминание #{reminder_id} установлено.\n"
                         f"📅 {remind_time.strftime('%d.%m %H:%M')} (Киевское время)",
                         reply_markup=main_menu())

async def send_reminder(chat_id, reminder_id):
    """Отправляет напоминание и удаляет его из списка"""
    if chat_id in reminders:
        for reminder in reminders[chat_id]:
            if reminder[0] == reminder_id:
                await bot.send_message(chat_id, f"🔔 Напоминание: {reminder[2]}")
                reminders[chat_id].remove(reminder)
                break

async def main():
    scheduler.start()
    print("✅ Бот успешно запущен! Можно использовать /start.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
