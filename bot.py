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
                         "📌 Чтобы установить напоминание, используй:\n"
                         "`/time 30m Сделать зарядку` – через время\n"
                         "`/time 2h Позвонить другу` – через часы\n"
                         "`/time 15.02 18:30 Встреча` – на дату и время\n\n"
                         "Пример: `/time 10m Перекусить 🍏`", parse_mode="Markdown")

@dp.message(Command("time"))
async def time_handler(message: types.Message):
    """Обрабатывает установку напоминания через время или по дате"""
    args = message.text.split(maxsplit=2)  # 🟢 Разбиваем текст: /time 30m ТЕКСТ или /time 15.02 18:30 ТЕКСТ

    if len(args) < 3:
        await message.answer("⚠️ Формат команды: `/time 30m ТЕКСТ` или `/time 15.02 18:30 ТЕКСТ`\n\nПример:\n"
                             "`/time 10m Перекусить 🍏`\n"
                             "`/time 15.02 18:30 Встреча`", parse_mode="Markdown")
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
        reminder_type = f"через {amount}{unit}"

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

        reminder_type = f"на {remind_time.strftime('%d.%m %H:%M')}"

    else:
        await message.answer("❌ Ошибка: неверный формат времени!\nИспользуй `30m`, `2h` или `дд.мм чч:мм`.", parse_mode="Markdown")
        return

    # ✅ Добавляем напоминание в список
    reminder_id = len(reminders.get(chat_id, [])) + 1
    if chat_id not in reminders:
        reminders[chat_id] = []
    reminders[chat_id].append((reminder_id, remind_time, text))

    scheduler.add_job(send_reminder, "date", run_date=remind_time, args=[chat_id, reminder_id])

    await message.answer(f"✅ Напоминание #{reminder_id} установлено {reminder_type}.\n"
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
