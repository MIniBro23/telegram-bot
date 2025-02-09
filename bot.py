import asyncio
import os
import re
import pytz
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
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

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка. 🕒\n\n"
                         "📌 Чтобы установить напоминание, используй команду:\n"
                         "`/time 30m Сделать зарядку`\n"
                         "`/time 2h Позвонить другу`\n\n"
                         "Пример: `/time 10m Перекусить 🍏`", parse_mode="Markdown")

@dp.message(Command("time"))
async def time_handler(message: types.Message):
    """Обрабатывает установку напоминания через время"""
    args = message.text.split(maxsplit=2)  # 🟢 Разбиваем текст: /time 30m ТЕКСТ

    if len(args) < 3:
        await message.answer("⚠️ Формат команды: `/time 30m ТЕКСТ`\n\nПример:\n"
                             "`/time 10m Перекусить 🍏`\n"
                             "`/time 2h Встреча с другом`", parse_mode="Markdown")
        return

    time_str, text = args[1], args[2]

    # ✅ Проверяем, это "30m" или "2h"
    match = re.match(r"^(\d+)([mh])$", time_str)

    if not match:
        await message.answer("❌ Ошибка: неверный формат времени!\nИспользуй `30m` или `2h`.", parse_mode="Markdown")
        return

    amount, unit = int(match.group(1)), match.group(2)
    delay = amount * 60 if unit == "m" else amount * 3600
    remind_time = datetime.now(KYIV_TZ) + timedelta(seconds=delay)

    chat_id = message.chat.id
    reminder_id = len(reminders.get(chat_id, [])) + 1
    if chat_id not in reminders:
        reminders[chat_id] = []
    reminders[chat_id].append((reminder_id, remind_time, text))

    scheduler.add_job(send_reminder, "date", run_date=remind_time, args=[chat_id, reminder_id])

    await message.answer(f"✅ Напоминание #{reminder_id} установлено через {amount}{unit}.\n"
                         f"📅 {remind_time.strftime('%H:%M')} (Киевское время)")

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
    print("✅ Бот успешно запущен! Можно использовать /start и /time.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
