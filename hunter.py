#!/usr/bin/env python3
"""
Avito Hunter — автоматический парсер клиентов для персональных тренировок.
Полностью совместим с Termux, без input(), без меню, с антибаном.
"""

import os
import random
import time
import logging
import json
from pathlib import Path
from typing import Set

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ────────────────────────────────────────────────
#  ЛОГИРОВАНИЕ
# ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-5s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger("hunter")

# ────────────────────────────────────────────────
#  ЗАГРУЗКА .env
# ────────────────────────────────────────────────
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    logger.error("❌ TELEGRAM_TOKEN или TELEGRAM_CHAT_ID отсутствуют в .env")
    exit(1)

# ────────────────────────────────────────────────
#  НАСТРОЙКИ
# ────────────────────────────────────────────────
CITIES = ["abakan", "minusinsk", "chernogorsk"]
QUERY = "тренер"

CLIENT_PATTERNS = [
    r'ищу\s+трен(ер|ера|ершу)?',
    r'нужен\s+трен(ер|ера|ершу)?',
    r'(нужен|ищу)\s+пт\s',
    r'ищу\s+пт',
    r'тренировк[аи]',
    r'персональн(ый|ая|ые|ых)\s+трен',
    r'индивидуальн(ые|ый)\s+занятия',
]

MIN_PRICE = 0
MAX_PRICE = 20000

HISTORY_FILE = Path("seen_items.json")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) Safari/605.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2) Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) Chrome/122.0 Mobile",
]

MIN_DELAY_ITEMS = (0.7, 2.1)
MIN_DELAY_CITIES = (3, 8)
MIN_DELAY_CYCLES = (20 * 60, 32 * 60)

# ────────────────────────────────────────────────
#  ИНИЦИАЛИЗАЦИЯ
# ────────────────────────────────────────────────
session = requests.Session()

session.headers.update({
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.avito.ru/",
})

seen: Set[str] = set()

if HISTORY_FILE.exists():
    try:
        seen = set(json.load(open(HISTORY_FILE, encoding="utf-8")))
        logger.info(f"📁 Загружено {len(seen)} объявлений из истории")
    except:
        logger.warning("⚠️ Не удалось загрузить историю")


def save_seen():
    try:
        json.dump(list(seen), open(HISTORY_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка сохранения истории: {e}")


def sleep_range(a, b):
    time.sleep(random.uniform(a, b))


def headers_rotated():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": random.choice([
            "ru-RU,ru;q=0.9",
            "ru;q=0.9,en;q=0.8",
            "ru-RU,ru;q=0.8,en-US;q=0.5",
        ]),
        "Referer": random.choice([
            "https://www.avito.ru/",
            "https://www.google.com/",
            "https://yandex.ru/search/",
        ]),
        "Accept": random.choice([
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "text/html,application/xml;q=0.9,*/*;q=0.7",
        ]),
        "Connection": random.choice(["keep-alive", "close"]),
    }


def tg(method, data):
    try:
        r = session.post(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data, timeout=10)
        return r.status_code == 200
    except:
        return False


def notify(text):
    tg("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    })


def notify_photo(url, caption):
    tg("sendPhoto", {
        "chat_id": CHAT_ID,
        "photo": url,
        "caption": caption,
        "parse_mode": "HTML",
    })


# ────────────────────────────────────────────────
#  ПАРСИНГ ГОРОДА
# ────────────────────────────────────────────────
def parse_city(city: str):
    rnd = random.randint(100000, 999999)
    url = f"https://www.avito.ru/{city}?q={QUERY.replace(' ', '+')}&_={rnd}"

    headers = headers_rotated()
    logger.info(f"→ {city.upper():10}  {url}")
    logger.info(f"UA: {headers['User-Agent']}")

    try:
        r = session.get(url, headers=headers, timeout=14)

        if "captcha" in r.url.lower() or "проверка" in r.text.lower():
            logger.warning("⚠️ Капча! Сброс cookies + пауза 8–15 мин")
            session.cookies.clear()
            sleep_range(480, 900)
            return

        if r.status_code != 200:
            logger.warning(f"Статус {r.status_code} → пропуск")
            return

        soup = BeautifulSoup(r.text, "html.parser")

        items = soup.select('div[data-marker="item"]')
        if not items:
            logger.warning("Fallback → ищем .iva-item-root")
            items = soup.select("div.iva-item-root")

        items = items[:18]

        for item in items:
            sleep_range(*MIN_DELAY_ITEMS)

            item_id = item.get("data-item-id") or item.get("id")
            if not item_id or item_id in seen:
                continue

            title_a = (
                item.select_one('a[data-marker="item-title"]')
                or item.select_one("a.iva-item-title")
                or item.select_one("a.link-link-MbQDP")
            )
            if not title_a:
                continue

            title = title_a.get_text(strip=True)
            link = title_a.get("href", "")
            if link.startswith("/"):
                link = "https://www.avito.ru" + link

            price_meta = item.select_one('meta[itemprop="price"]')
            price = int(price_meta["content"]) if price_meta and price_meta.get("content", "").isdigit() else 0

            if not (MIN_PRICE <= price <= MAX_PRICE):
                continue

            text_lower = title.lower()
            if not any(re.search(p, text_lower) for p in CLIENT_PATTERNS):
                continue

            img = (
                item.select_one("img.photo-slider-list-item__image")
                or item.select_one("img.iva-item-sliderImage")
                or item.select_one("img")
            )
            photo = img.get("src") or img.get("data-src") if img else None

            caption = (
                f"<b>КЛИЕНТ • {city.upper()}</b>\n\n"
                f"{title}\n"
                f"💰 {price:,} ₽\n\n"
                f"<a href=\"{link}\">Открыть объявление</a>\n\n"
                f"🔥 <b>ОТВЕЧАЙ БЫСТРО!</b>"
            )

            if photo:
                notify_photo(photo, caption)
            else:
                notify(caption)

            seen.add(item_id)
            save_seen()
            logger.info(f"Найден клиент → {title[:70]}")

    except Exception as e:
        logger.error(f"Ошибка парсинга {city}: {e}")


# ────────────────────────────────────────────────
#  ГЛАВНЫЙ ЦИКЛ
# ────────────────────────────────────────────────
def main():
    notify("🟢 <b>Avito Hunter запущен</b>")

    while True:
        random.shuffle(CITIES)

        for city in CITIES:
            parse_city(city)
            sleep_range(*MIN_DELAY_CITIES)

        mins = random.randint(*MIN_DELAY_CYCLES) // 60
        logger.info(f"Цикл завершён → следующий через ~{mins} мин")
        sleep_range(*MIN_DELAY_CYCLES)


if __name__ == "__main__":
    main()
