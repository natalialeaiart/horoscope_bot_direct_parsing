#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL для получения гороскопов
HOROSCOPE_URL = "https://www.astrology.com/horoscope/daily.html"

# Словарь с соответствием знаков зодиака на английском и русском
ZODIAC_SIGNS = {
    "aries": "Овен",
    "taurus": "Телец",
    "gemini": "Близнецы",
    "cancer": "Рак",
    "leo": "Лев",
    "virgo": "Дева",
    "libra": "Весы",
    "scorpio": "Скорпион",
    "sagittarius": "Стрелец",
    "capricorn": "Козерог",
    "aquarius": "Водолей",
    "pisces": "Рыбы"
}

class HoroscopeParser:
    """Класс для парсинга гороскопов с сайта astrology.com"""
    
    def __init__(self):
        """Инициализация парсера"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_all_horoscopes(self) -> Dict[str, str]:
        """
        Получает гороскопы для всех знаков зодиака
        
        Returns:
            Dict[str, str]: Словарь с гороскопами, где ключ - знак зодиака, значение - текст гороскопа
        """
        try:
            logger.info("Fetching horoscopes from astrology.com")
            
            # Получаем HTML-страницу
            response = self.session.get(HOROSCOPE_URL)
            response.raise_for_status()
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Словарь для хранения гороскопов
            horoscopes = {}
            
            # Находим все блоки с гороскопами
            horoscope_blocks = soup.find_all('div', class_='horoscope-content')
            
            if not horoscope_blocks:
                # Альтернативный поиск, если структура сайта изменилась
                horoscope_blocks = soup.find_all('a', class_='horoscope-card')
            
            if not horoscope_blocks:
                logger.error("Could not find horoscope blocks on the page")
                return {}
            
            # Извлекаем гороскопы для каждого знака
            for block in horoscope_blocks:
                sign = None
                text = None
                
                # Пытаемся найти знак зодиака
                sign_elem = block.find('h3') or block.find('h2') or block.find('span', class_='sign-name')
                if sign_elem:
                    sign = sign_elem.text.strip().lower()
                
                # Пытаемся найти текст гороскопа
                text_elem = block.find('p') or block.find('div', class_='horoscope-text')
                if text_elem:
                    text = text_elem.text.strip()
                
                # Если не нашли текст, пробуем получить весь текст блока
                if not text:
                    text = block.text.strip()
                    # Удаляем "Read More" и подобные фразы
                    text = text.replace("Read More", "").strip()
                
                # Если нашли и знак, и текст, добавляем в словарь
                if sign and text and sign in ZODIAC_SIGNS.keys():
                    horoscopes[sign] = text
            
            # Проверяем, что получили все гороскопы
            if len(horoscopes) < 12:
                logger.warning(f"Only found {len(horoscopes)} horoscopes instead of 12")
                
                # Если не нашли все гороскопы, пробуем альтернативный метод
                if len(horoscopes) == 0:
                    return self._alternative_parsing(soup)
            
            logger.info(f"Successfully fetched {len(horoscopes)} horoscopes")
            return horoscopes
            
        except Exception as e:
            logger.error(f"Error fetching horoscopes: {e}")
            return {}
    
    def _alternative_parsing(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Альтернативный метод парсинга, если основной не сработал
        
        Args:
            soup: BeautifulSoup объект с HTML-страницей
            
        Returns:
            Dict[str, str]: Словарь с гороскопами
        """
        horoscopes = {}
        
        try:
            # Ищем все ссылки, которые могут содержать гороскопы
            links = soup.find_all('a')
            
            for sign in ZODIAC_SIGNS.keys():
                for link in links:
                    # Проверяем, содержит ли ссылка название знака
                    if sign in link.text.lower():
                        # Извлекаем текст и очищаем его
                        text = link.text.strip()
                        # Удаляем название знака из текста
                        for zodiac in ZODIAC_SIGNS.keys():
                            if zodiac in text.lower():
                                text = text.lower().replace(zodiac, "", 1)
                                break
                        
                        # Удаляем "Read More" и подобные фразы
                        text = text.replace("read more", "").strip()
                        
                        if text:
                            horoscopes[sign] = text
                            break
            
            logger.info(f"Alternative parsing found {len(horoscopes)} horoscopes")
            return horoscopes
            
        except Exception as e:
            logger.error(f"Error in alternative parsing: {e}")
            return {}
    
    def get_horoscope_for_sign(self, sign: str) -> Optional[str]:
        """
        Получает гороскоп для конкретного знака зодиака
        
        Args:
            sign: Знак зодиака на английском (lowercase)
            
        Returns:
            Optional[str]: Текст гороскопа или None, если не удалось получить
        """
        if sign not in ZODIAC_SIGNS:
            logger.error(f"Invalid zodiac sign: {sign}")
            return None
        
        horoscopes = self.get_all_horoscopes()
        return horoscopes.get(sign)

# Для тестирования
if __name__ == "__main__":
    parser = HoroscopeParser()
    horoscopes = parser.get_all_horoscopes()
    
    for sign, text in horoscopes.items():
        print(f"{ZODIAC_SIGNS[sign]}: {text[:100]}...")
