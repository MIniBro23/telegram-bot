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

# 📌 Главное меню с кнопками
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить напоминание", callback_data="add_reminder")],
        [InlineKeyboardButton(text="📜 История", callback_data="history")],
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

@dp.callback_query(lambda c: c.data == "history")
async def show_history(callback_query: types.CallbackQuery):
    """Показать список напоминаний"""
    chat_id = callback_query.from_user.id
    if chat_id not in reminders or not reminders[chat_id]:
        await callback_query.message.edit_text("📜 У тебя нет активных напоминаний.", reply_markup=main_menu())
        return
    
    history_text = "📜 **Твои напоминания:**\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for i, (reminder_id, remind_time, text) in enumerate(reminders[chat_id], 1):
        history_text += f"📌 {i}. {remind_time.strftime('%d.%m %H:%M')} – {text}\n"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"❌ Удалить {i}", callback_data=f"delete_{reminder_id}")
        ])

    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back")])
    await callback_query.message.edit_text(history_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_reminder(callback_query: types.CallbackQuery):
    """Удаление напоминания"""
    chat_id = callback_query.from_user.id
    reminder_id = int(callback_query.data.split("_")[1])

    if chat_id in reminders:
        reminders[chat_id] = [r for r in reminders[chat_id] if r[0] != reminder_id]
        await callback_query.answer(f"✅ Напоминание #{reminder_id} удалено!")
        await show_history(callback_query)

@dp.callback_query(lambda c: c.data == "back")
async def back_to_main(callback_query: types.CallbackQuery):
    """Вернуться в главное меню"""
    await callback_query.message.edit_text("📌 Используй кнопки ниже:", reply_markup=main_menu())

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
