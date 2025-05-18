#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Dict, Optional

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Словарь знаков зодиака EN→RU
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
    BASE_URL = "https://www.astrology.com/horoscope/daily"

    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _make_request(self, url: str) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None

    def get_horoscope(self, sign: str) -> Optional[str]:
        if sign not in ZODIAC_SIGNS:
            logger.error(f"Invalid zodiac sign: {sign}")
            return None

        url = f"{self.BASE_URL}/{sign}.html"
        html = self._make_request(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Актуальный способ: ищем просто самый длинный параграф
            paragraphs = soup.find_all('p')
            # Выбираем самый длинный параграф (скорее всего, это гороскоп)
            horoscope_text = ""
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > len(horoscope_text):
                    horoscope_text = text
            if horoscope_text and len(horoscope_text) > 80:
                return horoscope_text

            logger.error(f"Could not find horoscope text for {sign}")
            return None

        except Exception as e:
            logger.error(f"Error parsing horoscope for {sign}: {e}")
            return None

    def get_all_horoscopes(self) -> Dict[str, str]:
        result = {}
        for sign in ZODIAC_SIGNS:
            logger.info(f"Fetching horoscope for {sign}")
            horoscope = self.get_horoscope(sign)
            if horoscope:
                result[sign] = horoscope
            else:
                logger.warning(f"Failed to get horoscope for {sign}")
        return result

# Для тестирования
if __name__ == "__main__":
    parser = HoroscopeParser()
    horoscopes = parser.get_all_horoscopes()
    for sign, text in horoscopes.items():
        print(f"=== {ZODIAC_SIGNS[sign]} ===")
        print(text[:180] + "..." if len(text) > 180 else text)
        print()
