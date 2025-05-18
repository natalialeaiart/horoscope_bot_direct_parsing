#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import time
import argparse
import asyncio
from datetime import datetime
import pytz
from typing import Dict, Optional

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

from parser import HoroscopeParser, ZODIAC_SIGNS
from translator import HoroscopeTranslator

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("horoscope_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --------- ВАЖНО: тут правильный username ---------
bot_username = os.getenv("BOT_USERNAME", "moondosebot")  # Имя твоего нового бота без @

def make_zodiac_keyboard(bot_username):
    keyboard = []
    signs = list(ZODIAC_SIGNS.items())
    row = []
    for i, (sign_id, sign_name) in enumerate(signs):
        url = f"https://t.me/{bot_username}?start={sign_id}"
        row.append(InlineKeyboardButton(sign_name, url=url))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)
    
class HoroscopeBot:
    """Основной класс Telegram-бота для гороскопов"""

    def __init__(self, telegram_token: str, channel_id: str, openai_api_key: Optional[str] = None):
        self.telegram_token = telegram_token
        self.channel_id = channel_id
        self.openai_api_key = openai_api_key
        self.parser = HoroscopeParser()
        self.translator = HoroscopeTranslator(api_key=openai_api_key)
        self.horoscopes_cache = {}

    async def fetch_and_translate_horoscopes(self) -> Dict[str, str]:
        try:
            logger.info("Fetching horoscopes from astrology.com")
            horoscopes_en = self.parser.get_all_horoscopes()
            if not horoscopes_en:
                logger.error("Failed to fetch horoscopes")
                return {}
            logger.info(f"Successfully fetched {len(horoscopes_en)} horoscopes")
            logger.info("Translating horoscopes to Russian")
            horoscopes_ru = self.translator.translate_horoscopes(horoscopes_en)
            if not horoscopes_ru:
                logger.error("Failed to translate horoscopes")
                return {}
            logger.info(f"Successfully translated {len(horoscopes_ru)} horoscopes")
            self.horoscopes_cache = horoscopes_ru
            return horoscopes_ru
        except Exception as e:
            logger.error(f"Error fetching and translating horoscopes: {e}")
            return {}

    async def send_daily_post(self) -> None:
        try:
            months_ru = [
                'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
                'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'
            ]
            now = datetime.now(pytz.timezone('Europe/Riga'))
            date_str = f"{now.day} {months_ru[now.month - 1]}, {now.year}"

            message_text = (
                f"Дата: {date_str}\n\n"
                "Астрологический прогноз дня.\n\n"
                "Выбери свой знак зодиака и получи персональный прогноз в личных сообщениях:"
            )

            reply_markup = make_zodiac_keyboard(bot_username)

            application = Application.builder().token(self.telegram_token).build()
            async with application:
                await application.bot.send_message(
                    chat_id=self.channel_id,
                    text=message_text,
                    reply_markup=reply_markup
                )

            logger.info("Daily post sent successfully")

        except Exception as e:
            logger.error(f"Failed to send daily post: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        args = context.args
        if args:
            sign = args[0].lower()
            if sign in ZODIAC_SIGNS:
                # Кэшируем гороскопы, чтобы не дергать каждый раз
                if not self.horoscopes_cache:
                    self.horoscopes_cache = await self.fetch_and_translate_horoscopes()
                horoscope = self.horoscopes_cache.get(sign)
                zodiac_name = ZODIAC_SIGNS[sign]
                if horoscope:
                    await update.message.reply_text(
                        f"Твой гороскоп на сегодня для знака {zodiac_name}:\n\n{horoscope}"
                    )
                    return
        await update.message.reply_text(
            "Привет! Я бот-гороскоп. Выбери свой знак зодиака из канала и получи персональный прогноз."
        )

    async def run_bot(self) -> None:
        try:
            application = Application.builder().token(self.telegram_token).build()
            application.add_handler(CommandHandler("start", self.start))
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            logger.info("Bot started in polling mode")
            while True:
                await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            if 'application' in locals():
                await application.stop()
                await application.shutdown()

async def main() -> None:
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not telegram_token or not channel_id or not openai_api_key:
        logger.error("TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID or OPENAI_API_KEY not set")
        return

    parser = argparse.ArgumentParser(description="Horoscope Bot Service")
    parser.add_argument("--daily-post", action="store_true", help="Send daily post with zodiac buttons")
    parser.add_argument("--run-bot", action="store_true", help="Run bot in polling mode")
    args = parser.parse_args()

    bot = HoroscopeBot(telegram_token, channel_id, openai_api_key)

    if args.daily_post:
        await bot.send_daily_post()
    elif args.run_bot:
        await bot.run_bot()
    else:
        logger.error("No action specified. Use --daily-post or --run-bot")

if __name__ == "__main__":
    asyncio.run(main())
