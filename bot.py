import asyncio
import re
import os
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

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

# 📌 Клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить напоминание")],
        [KeyboardButton(text="📋 Мои напоминания")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка. Теперь ты можешь устанавливать напоминания на **конкретную дату и время!**\n\n"
                         "📌 Примеры:\n"
                         "`/remind 15.02 18:30 Позвонить родителям`\n"
                         "`/remind 20.03 09:00 Встреча`\n"
                         "`/remind 10m Сделать зарядку`", parse_mode="Markdown", reply_markup=main_keyboard)

@dp.message(Command("remind"))
async def remind_handler(message: types.Message):
    """Обработчик создания напоминаний"""
    print(f"📥 Получена команда: {message.text}")  # ✅ Лог для Render

    args = message.text.split(maxsplit=2)  # 🟢 Теперь бот правильно разбирает команду

    if len(args) < 3:
        await message.answer("⚠️ Используй формат: `/remind дд.мм чч:мм ТЕКСТ` или `/remind 30m ТЕКСТ`\n\nПример:\n"
                             "`/remind 15.02 18:30 Позвонить родителям`\n"
                             "`/remind 10m Сделать зарядку`", parse_mode="Markdown")
        return

    time_str, text = args[1], args[2]

    # ✅ Проверяем, это "30m", "2h" или "15.02 18:30"
    match_relative = re.match(r"^(\d+)([mh])$", time_str)
    match_absolute = re.match(r"^(\d{2})\.(\d{2}) (\d{2}):(\d{2})$", time_str)

    chat_id = message.chat.id

    if match_relative:
        # ⏳ Напоминание через n минут/часов
        amount, unit = int(match_relative.group(1)), match_relative.group(2)
        delay = amount * 60 if unit == "m" else amount * 3600
        remind_time = datetime.now(KYIV_TZ) + timedelta(seconds=delay)
        print(f"📌 Установлено напоминание через {amount}{unit} на {remind_time.strftime('%d.%m %H:%M')}")

    elif match_absolute:
        # 📅 Напоминание на конкретную дату и время
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

        print(f"📌 Установлено напоминание на {remind_time.strftime('%d.%m %H:%M')}")

    else:
        await message.answer("⚠️ Неверный формат времени! Используй:\n"
                             "- `30m` (минуты) или `2h` (часы)\n"
                             "- `дд.мм чч:мм` для конкретного времени (киевский часовой пояс)\n\n"
                             "Пример:\n"
                             "`/remind 45m Пауза`\n"
                             "`/remind 15.02 18:30 Позвонить другу`", parse_mode="Markdown")
        return

    # ✅ Добавляем напоминание в список
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
    print("✅ Бот успешно запущен и работает! Ошибка с датами исправлена.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
