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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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

class HoroscopeBot:
    """Основной класс Telegram-бота для гороскопов"""
    
    def __init__(self, telegram_token: str, channel_id: str, openai_api_key: Optional[str] = None):
        """
        Инициализация сервиса
        
        Args:
            telegram_token: Токен Telegram бота
            channel_id: ID канала для публикации ежедневных постов
            openai_api_key: API ключ OpenAI (если None, берется из переменной окружения OPENAI_API_KEY)
        """
        self.telegram_token = telegram_token
        self.channel_id = channel_id
        self.openai_api_key = openai_api_key
        
        # Инициализация парсера и переводчика
        self.parser = HoroscopeParser()
        self.translator = HoroscopeTranslator(api_key=openai_api_key)
        
        # Кэш для хранения гороскопов
        self.horoscopes_cache = {}
        
    async def fetch_and_translate_horoscopes(self) -> Dict[str, str]:
        """
        Получает и переводит гороскопы для всех знаков зодиака
        
        Returns:
            Dict[str, str]: Словарь с переведенными гороскопами
        """
        try:
            logger.info("Fetching horoscopes from astrology.com")
            
            # Получаем гороскопы на английском
            horoscopes_en = self.parser.get_all_horoscopes()
            
            if not horoscopes_en:
                logger.error("Failed to fetch horoscopes")
                return {}
            
            logger.info(f"Successfully fetched {len(horoscopes_en)} horoscopes")
            
            # Переводим гороскопы на русский
            logger.info("Translating horoscopes to Russian")
            horoscopes_ru = self.translator.translate_horoscopes(horoscopes_en)
            
            if not horoscopes_ru:
                logger.error("Failed to translate horoscopes")
                return {}
            
            logger.info(f"Successfully translated {len(horoscopes_ru)} horoscopes")
            
            # Сохраняем в кэш
            self.horoscopes_cache = horoscopes_ru
            
            return horoscopes_ru
            
        except Exception as e:
            logger.error(f"Error fetching and translating horoscopes: {e}")
            return {}
    
    async def send_daily_post(self) -> None:
        """Отправляет ежедневный пост с кнопками выбора знака зодиака"""
        try:
            # Получаем и переводим гороскопы
            horoscopes = await self.fetch_and_translate_horoscopes()
            if not horoscopes:
                logger.error("Cannot send daily post: No horoscopes available")
                return
            
            # Формируем текущую дату в формате "18 Мая, 2025"
            months_ru = [
                'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
                'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'
            ]
            now = datetime.now(pytz.timezone('Europe/Riga'))
            date_str = f"{now.day} {months_ru[now.month - 1]}, {now.year}"
            
            # Создаем текст сообщения
            message_text = f"Дата: {date_str}\n\nАстрологический прогноз дня.\n\nВыбери свой знак зодиака:"
            
            # Создаем клавиатуру с кнопками знаков зодиака
            keyboard = []
            row = []
            for i, (sign_id, sign_name) in enumerate(ZODIAC_SIGNS.items()):
                row.append(InlineKeyboardButton(sign_name, callback_data=f"horoscope:{sign_id}"))
                if (i + 1) % 3 == 0:  # По 3 кнопки в ряду
                    keyboard.append(row)
                    row = []
            
            if row:  # Добавляем оставшиеся кнопки
                keyboard.append(row)
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение в канал
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
    
    async def handle_sign_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает выбор знака зодиака"""
        query = update.callback_query
        await query.answer()
        
        # Получаем выбранный знак из callback_data
        callback_data = query.data
        if not callback_data.startswith("horoscope:"):
            return
            
        sign_id = callback_data.split(":")[1]
        
        # Если кэш пуст, получаем и переводим гороскопы
        if not self.horoscopes_cache:
            self.horoscopes_cache = await self.fetch_and_translate_horoscopes()
            
        # Получаем гороскоп для выбранного знака
        horoscope = self.horoscopes_cache.get(sign_id)
        if not horoscope:
            await query.message.reply_text("Извините, гороскоп для этого знака временно недоступен.")
            return
            
        # Отправляем гороскоп пользователю
        sign_name = ZODIAC_SIGNS.get(sign_id, sign_id)
        await query.message.reply_text(f"*{sign_name}*\n\n{horoscope}", parse_mode="Markdown")
        
    async def run_bot(self) -> None:
        """Запускает бота в режиме обработки команд"""
        try:
            # Создаем и настраиваем приложение
            application = Application.builder().token(self.telegram_token).build()
            
            # Добавляем обработчик для кнопок
            application.add_handler(CallbackQueryHandler(self.handle_sign_selection))
            
            # Запускаем бота
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            logger.info("Bot started in polling mode")
            
            # Держим бота запущенным
            while True:
                await asyncio.sleep(3600)  # Проверка каждый час
                
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            
        finally:
            # Корректно останавливаем бота при выходе
            if 'application' in locals():
                await application.stop()
                await application.shutdown()

async def main() -> None:
    """Основная функция для запуска бота"""
    # Получаем переменные окружения
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not telegram_token or not channel_id or not openai_api_key:
        logger.error("TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID or OPENAI_API_KEY not set")
        return
    
    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Horoscope Bot Service")
    parser.add_argument("--daily-post", action="store_true", help="Send daily post with zodiac buttons")
    parser.add_argument("--run-bot", action="store_true", help="Run bot in polling mode")
    
    args = parser.parse_args()
    
    # Создаем экземпляр бота
    bot = HoroscopeBot(telegram_token, channel_id, openai_api_key)
    
    if args.daily_post:
        # Отправляем ежедневный пост
        await bot.send_daily_post()
    elif args.run_bot:
        # Запускаем бота в режиме обработки команд
        await bot.run_bot()
    else:
        logger.error("No action specified. Use --daily-post or --run-bot")

if __name__ == "__main__":
    asyncio.run(main())
