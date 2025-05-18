#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
from bs4 import BeautifulSoup
from typing import Dict, Optional

# Соответствие знаков зодиака на английском и русском
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

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        Получает гороскопы для всех знаков зодиака с обновлённой структуры сайта astrology.com.
        Returns:
            Dict[str, str]: Словарь с гороскопами, где ключ - знак зодиака, значение - текст гороскопа
        """
        horoscopes = {}
        base_url = "https://www.astrology.com/horoscope/daily/{}.html"
        for sign in ZODIAC_SIGNS.keys():
            try:
                url = base_url.format(sign)
                logger.info(f"Fetching horoscope for {sign} from {url}")
                response = self.session.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                # В новой структуре гороскоп — это первый <p> внутри <div class="horoscope-main-content">
                content_div = soup.find('div', class_='horoscope-main-content')
                if content_div:
                    p = content_div.find('p')
                    if p and p.text.strip():
                        horoscopes[sign] = p.text.strip()
                    else:
                        logger.warning(f"Could not find horoscope text for {sign}")
                else:
                    logger.warning(f"Could not find content div for {sign}")
            except Exception as e:
                logger.error(f"Error fetching horoscope for {sign}: {e}")
        logger.info(f"Successfully fetched {len(horoscopes)} horoscopes")
        return horoscopes

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

# Пример теста (можно запускать отдельно)
if __name__ == "__main__":
    parser = HoroscopeParser()
    horoscopes = parser.get_all_horoscopes()
    for sign, text in horoscopes.items():
        print(f"{ZODIAC_SIGNS[sign]}: {text[:100]}...\n")
