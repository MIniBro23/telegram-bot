import asyncio
import os
from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from aiogram.webhook.aiohttp_server import setup_application
from aiohttp import web

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = "https://your-app-name.onrender.com/webhook"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.post("/webhook")
async def telegram_webhook(update: dict):
    await dp.feed_webhook_data(update)
    return {"ok": True}

if __name__ == "__main__":
    web.run_app(setup_application(dp, app), port=8000)
