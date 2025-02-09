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
    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        await message.answer("⚠️ Используй формат: `/remind дд.мм чч:мм ТЕКСТ` или `/remind 30m ТЕКСТ`\n\nПример:\n"
                             "`/remind 15.02 18:30 Позвонить родителям`\n"
                             "`/remind 10m Сделать зарядку`", parse_mode="Markdown")
        return

    time_str, text = args[1], args[2]

    # Проверяем, это формат "30m" / "2h" или конкретная дата "15.02 18:30"
    match_relative = re.match(r"(\d+)([mh])", time_str)
    match_absolute = re.match(r"(\d{2})\.(\d{2}) (\d{2}):(\d{2})", time_str)

    chat_id = message.chat.id

    if match_relative:
        # Напоминание в минутах/часах
        amount, unit = int(match_relative.group(1)), match_relative.group(2)
        delay = amount * 60 if unit == "m" else amount * 3600
        remind_time = datetime.now(KYIV_TZ) + timedelta(seconds=delay)
    
    elif match_absolute:
        # Напоминание на конкретную дату и время
        day, month, hour, minute = map(int, match_absolute.groups())
        now = datetime.now(KYIV_TZ)
        year = now.year

        try:
            remind_time = KYIV_TZ.localize(datetime(year, month, day, hour, minute))
        except ValueError:
            await message.answer("❌ Ошибка: Некорректная дата или время.")
            return

        if remind_time < now:
            await message.answer("⚠️ Ошибка: Нельзя установить напоминание в прошлом!")
            return

    else:
        await message.answer("⚠️ Неверный формат времени! Используй:\n"
                             "- `30m` (минуты) или `2h` (часы)\n"
                             "- `дд.мм чч:мм` для конкретного времени (киевский часовой пояс)\n\n"
                             "Пример:\n"
                             "`/remind 45m Пауза`\n"
                             "`/remind 15.02 18:30 Позвонить другу`", parse_mode="Markdown")
        return

    # Добавляем напоминание в список
    reminder_id = len(reminders.get(chat_id, [])) + 1
    if chat_id not in reminders:
        reminders[chat_id] = []
    reminders[chat_id].append((reminder_id, remind_time, text))

    scheduler.add_job(send_reminder, "date", run_date=remind_time, args=[chat_id, reminder_id])

    await message.answer(f"✅ Напоминание #{reminder_id} установлено на {remind_time.strftime('%d.%m %H:%M')} (Киевское время).")

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
    print("✅ Бот успешно запущен и работает! Поддержка выбора времени активирована.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
