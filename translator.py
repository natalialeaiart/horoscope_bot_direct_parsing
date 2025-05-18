#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import openai
from typing import Dict, List, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HoroscopeTranslator:
    """Класс для перевода гороскопов с помощью OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация переводчика
        
        Args:
            api_key: API ключ OpenAI (если None, берется из переменной окружения OPENAI_API_KEY)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OpenAI API key not provided and not found in environment variables")
            raise ValueError("OpenAI API key is required")
        
        # Инициализация клиента OpenAI
        openai.api_key = self.api_key
    
    def translate_horoscopes(self, horoscopes: Dict[str, str]) -> Dict[str, str]:
        """
        Переводит все гороскопы с английского на русский
        
        Args:
            horoscopes: Словарь с гороскопами на английском, где ключ - знак зодиака, значение - текст гороскопа
            
        Returns:
            Dict[str, str]: Словарь с переведенными гороскопами
        """
        translated_horoscopes = {}
        
        for sign, text in horoscopes.items():
            try:
                translated_text = self.translate_text(text)
                if translated_text:
                    translated_horoscopes[sign] = translated_text
                    logger.info(f"Successfully translated horoscope for {sign}")
                else:
                    logger.error(f"Failed to translate horoscope for {sign}")
            except Exception as e:
                logger.error(f"Error translating horoscope for {sign}: {e}")
        
        return translated_horoscopes
    
    def translate_text(self, text: str) -> Optional[str]:
        """
        Переводит текст с английского на русский с помощью OpenAI API
        
        Args:
            text: Текст для перевода
            
        Returns:
            Optional[str]: Переведенный текст или None, если произошла ошибка
        """
        if not text:
            logger.warning("Empty text provided for translation")
            return None
        
        try:
            # Формируем запрос к API
            prompt = f"Переведи следующий гороскоп с английского на русский. Сохрани стиль и тон оригинала, но сделай перевод естественным и читаемым на русском языке:\n\n{text}"
            
            # Отправляем запрос к API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Используем модель ChatGPT 4o mini
                messages=[
                    {"role": "system", "content": "Ты профессиональный переводчик с английского на русский, специализирующийся на астрологических текстах."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Извлекаем переведенный текст
            translated_text = response.choices[0].message.content.strip()
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {e}")
            return None

# Для тестирования
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Загружаем переменные окружения из .env файла
    load_dotenv()
    
    # Тестовый гороскоп
    test_horoscope = {
        "aries": "Today is a great day for new beginnings, Aries. Your energy is high and your enthusiasm is contagious."
    }
    
    # Создаем переводчик
    translator = HoroscopeTranslator()
    
    # Переводим гороскоп
    translated = translator.translate_horoscopes(test_horoscope)
    
    # Выводим результат
    for sign, text in translated.items():
        print(f"{sign}: {text}")
