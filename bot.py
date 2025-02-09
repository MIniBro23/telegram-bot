import asyncio
import re
import os
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

# ✅ Устанавливаем часовой пояс для Киева
KYIV_TZ = pytz.timezone("Europe/Kiev")

# ✅ Получаем токен из переменной окружения (должен быть в Render!)
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ Ошибка: переменная окружения TOKEN не установлена!")

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# 📌 Хранение напоминаний (по chat_id)
reminders = {}

# 📌 Основная клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить напоминание")],
        [KeyboardButton(text="📋 Мои напоминания")]
    ],
    resize_keyboard=True
)

# 📌 Inline-кнопки выбора формата времени
reminder_type_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Через время (30m, 2h)", callback_data="remind_relative")],
        [InlineKeyboardButton(text="📅 По дате (15.02 18:30)", callback_data="remind_absolute")]
    ]
)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка. Теперь ты можешь устанавливать напоминания на **конкретную дату и время!**\n\n"
                         "📌 Примеры:\n"
                         "`/remind 15.02 18:30 Позвонить родителям`\n"
                         "`/remind 20.03 09:00 Встреча`\n"
                         "`/remind 10m Сделать зарядку`", parse_mode="Markdown", reply_markup=main_keyboard)

@dp.message(lambda message: message.text == "➕ Добавить напоминание")
async def add_reminder_handler(message: types.Message):
    """Запрос выбора формата времени"""
    await message.answer("Выбери, как установить напоминание:", reply_markup=reminder_type_keyboard)

@dp.callback_query(lambda c: c.data == "remind_relative")
async def ask_relative_time(callback: types.CallbackQuery):
    """Запрос времени в формате '30m' или '2h'"""
    await bot.send_message(callback.message.chat.id, "Введите напоминание в формате `30m Текст` или `2h Текст`.\n\nПример:\n"
                                                     "`30m Сделать зарядку`\n"
                                                     "`2h Позвонить другу`", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "remind_absolute")
async def ask_absolute_time(callback: types.CallbackQuery):
    """Запрос даты и времени в формате '15.02 18:30'"""
    await bot.send_message(callback.message.chat.id, "Введите напоминание в формате `дд.мм чч:мм Текст`.\n\nПример:\n"
                                                     "`15.02 18:30 Встреча`\n"
                                                     "`20.03 09:00 Совещание`", parse_mode="Markdown")

@dp.message(Command("remind"))
async def remind_handler(message: types.Message):
    """Обработчик создания напоминаний"""
    args = message.
