#!/data/data/com.termux/files/usr/bin/python3
"""
🚀 Avito Hunter PRO • Termux Edition
Полная версия для GitHub
"""

import os
import sys
import time
import random
import json
import re
import sqlite3
import signal
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

# ────────────────────────────────────────────────
#  📱 ТЕРМИНАЛЬНЫЙ ИНТЕРФЕЙС
# ────────────────────────────────────────────────
class TermuxUI:
    @staticmethod
    def clear():
        os.system('clear' if os.name == 'posix' else 'cls')
    
    @staticmethod
    def banner():
        print("""
╔══════════════════════════════════════╗
║      🚀 AVITO HUNTER PRO v2026       ║
║      📱 Терминал Termux Edition      ║
╚══════════════════════════════════════╝
""")
    
    @staticmethod
    def show_menu():
        print("\n" + "═" * 40)
        print("📋 МЕНЮ УПРАВЛЕНИЯ:")
        print("═" * 40)
        print("1. 🚀 Запустить парсер")
        print("2. ⏸️  Приостановить")
        print("3. 🔄 Перезагрузить")
        print("4. ⚙️  Настройки")
        print("5. 📊 Статистика")
        print("6. 📝 Логи")
        print("7. 🆘 Помощь")
        print("8. 🚪 Выход")
        print("═" * 40)
        return input("👉 Выберите действие (1-8): ").strip()

# ────────────────────────────────────────────────
#  ⚙️ КОНФИГУРАЦИОННЫЙ МЕНЕДЖЕР
# ────────────────────────────────────────────────
class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".avito_hunter"
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "telegram": {
                "token": "8313471489:AAH8dk-gSgT6zTiyjZvsQJd4om8Kov71XUg",
                "chat_id": "1066756284"
            },
            "search": {
                "cities": ["abakan", "minusinsk", "chernogorsk"],
                "query": "тренер",
                "min_price": 0,
                "max_price": 20000
            },
            "timing": {
                "delay_between_items": [0.5, 1.5],
                "delay_between_cities": [3, 8],
                "delay_between_cycles": [600, 1200]  # 10-20 минут
            },
            "patterns": {
                "client": [
                    "ищу тренер", "нужен тренер", 
                    "ищу пт", "персональный тренер",
                    "индивидуальные тренировки"
                ],
                "seller": [
                    "предлагаю", "услуги", "продам",
                    "набор", "обучение"
                ]
            }
        }
        
        self._ensure_config()
    
    def _ensure_config(self):
        """Создать директорию и файл конфигурации"""
        self.config_dir.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self.save_config(self.default_config)
    
    def load_config(self):
        """Загрузить конфигурацию"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return self.default_config.copy()
    
    def save_config(self, config):
        """Сохранить конфигурацию"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def edit_config_interactive(self):
        """Интерактивное редактирование конфигурации"""
        config = self.load_config()
        
        print("\n" + "═" * 40)
        print("⚙️  РЕДАКТИРОВАНИЕ КОНФИГУРАЦИИ")
        print("═" * 40)
        
        # Telegram
        print("\n📱 TELEGRAM:")
        token = input(f"Токен [{config['telegram']['token'][:10]}...]: ").strip()
        if token:
            config['telegram']['token'] = token
        
        chat_id = input(f"Chat ID [{config['telegram']['chat_id']}]: ").strip()
        if chat_id:
            config['telegram']['chat_id'] = chat_id
        
        # Поиск
        print("\n🔍 ПОИСК:")
        query = input(f"Запрос [{config['search']['query']}]: ").strip()
        if query:
            config['search']['query'] = query
        
        cities = input(f"Городы (через запятую) [{', '.join(config['search']['cities'])}]: ").strip()
        if cities:
            config['search']['cities'] = [c.strip() for c in cities.split(',')]
        
        # Цены
        try:
            min_price = input(f"Минимальная цена [{config['search']['min_price']}]: ").strip()
            if min_price:
                config['search']['min_price'] = int(min_price)
            
            max_price = input(f"Максимальная цена [{config['search']['max_price']}]: ").strip()
            if max_price:
                config['search']['max_price'] = int(max_price)
        except ValueError:
            print("⚠️  Ошибка: введите число")
        
        self.save_config(config)
        print("✅ Конфигурация сохранена!")
        return config

# ────────────────────────────────────────────────
#  🗄️ БАЗА ДАННЫХ
# ────────────────────────────────────────────────
class Database:
    def __init__(self):
        self.db_path = Path.home() / ".avito_hunter" / "hunter.db"
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        
        # Таблица просмотренных объявлений
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_items (
                id TEXT PRIMARY KEY,
                city TEXT,
                title TEXT,
                price INTEGER,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица статистики
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                date DATE PRIMARY KEY,
                leads INTEGER DEFAULT 0,
                scans INTEGER DEFAULT 0
            )
        """)
        
        # Таблица логов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                message TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_seen_item(self, item_id: str, city: str, title: str = "", price: int = 0):
        """Добавить просмотренное объявление"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT OR IGNORE INTO seen_items (id, city, title, price) VALUES (?, ?, ?, ?)",
                (item_id, city, title[:200], price)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Ошибка базы данных: {e}")
            return False
    
    def is_seen(self, item_id: str) -> bool:
        """Проверить, видели ли объявление"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT 1 FROM seen_items WHERE id = ? LIMIT 1", (item_id,))
            result = cursor.fetchone() is not None
            conn.close()
            return result
        except:
            return False
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        stats = {"total_seen": 0, "today_leads": 0, "total_leads": 0}
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Всего просмотрено
            cursor = conn.execute("SELECT COUNT(*) FROM seen_items")
            stats["total_seen"] = cursor.fetchone()[0]
            
            # Лиды за сегодня
            today = datetime.now().strftime("%Y-%m-%d")
            cursor = conn.execute(
                "SELECT SUM(leads) FROM stats WHERE date = ?",
                (today,)
            )
            stats["today_leads"] = cursor.fetchone()[0] or 0
            
            # Всего лидов
            cursor = conn.execute("SELECT SUM(leads) FROM stats")
            stats["total_leads"] = cursor.fetchone()[0] or 0
            
            conn.close()
        except Exception as e:
            print(f"⚠️  Ошибка получения статистики: {e}")
        
        return stats
    
    def log_event(self, level: str, message: str):
        """Записать событие в лог"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO logs (level, message) VALUES (?, ?)",
                (level, message[:500])
            )
            conn.commit()
            conn.close()
        except:
            pass

# ────────────────────────────────────────────────
#  🤖 ОСНОВНОЙ ПАРСЕР
# ────────────────────────────────────────────────
class AvitoHunter:
    def __init__(self, config: Dict, db: Database):
        self.config = config
        self.db = db
        self.running = False
        self.stats = {
            "current_cycle": 0,
            "leads_found": 0,
            "errors": 0
        }
        
        # Сессия requests
        self.session = requests.Session()
        self.session.headers.update({
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Referer": "https://www.avito.ru/",
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": self._get_user_agent()
        })
    
    def _get_user_agent(self) -> str:
        """Получить случайный User-Agent"""
        agents = [
            "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/122.0 Mobile",
            "Mozilla/5.0 (Android 14; Mobile) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2) Mobile Safari/604.1",
        ]
        return random.choice(agents)
    
    def send_telegram(self, message: str) -> bool:
        """Отправить сообщение в Telegram"""
        try:
            token = self.config['telegram']['token']
            chat_id = self.config['telegram']['chat_id']
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            response = self.session.post(url, data=data, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def is_client(self, title: str) -> bool:
        """Определить, является ли объявление клиентом"""
        title_lower = title.lower()
        
        # Проверка клиентских паттернов
        for pattern in self.config['patterns']['client']:
            if pattern.lower() in title_lower:
                return True
        
        # Проверка продавцов
        for pattern in self.config['patterns']['seller']:
            if pattern.lower() in title_lower:
                return False
        
        # Эвристики
        client_words = ["ищу", "нужен", "хочу", "ищется", "требуется", "нужна"]
        seller_words = ["продам", "предлагаю", "услуги", "набор", "запись"]
        
        client_score = sum(1 for word in client_words if word in title_lower)
        seller_score = sum(1 for word in seller_words if word in title_lower)
        
        return client_score > seller_score
    
    def parse_city(self, city: str) -> List[Dict]:
        """Спарсить объявления из города"""
        items = []
        
        try:
            # Формируем URL
            query = self.config['search']['query'].replace(' ', '+')
            url = f"https://www.avito.ru/{city}?q={query}&p=1"
            
            # Делаем запрос
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"⚠️  Ошибка HTTP {response.status_code} для {city}")
                return items
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Находим объявления
            item_blocks = soup.select('div[data-marker="item"]')
            
            for block in item_blocks[:20]:  # Ограничиваем
                # Извлекаем данные
                item_data = self._extract_item_data(block, city)
                if item_data:
                    items.append(item_data)
                
                # Пауза между объявлениями
                time.sleep(random.uniform(0.5, 1.5))
            
            self.db.log_event("INFO", f"Проверен город {city}, найдено {len(items)} объявлений")
            
        except Exception as e:
            error_msg = f"Ошибка при парсинге {city}: {str(e)}"
            print(f"❌ {error_msg}")
            self.db.log_event("ERROR", error_msg)
            self.stats["errors"] += 1
        
        return items
    
    def _extract_item_data(self, block, city: str) -> Optional[Dict]:
        """Извлечь данные из блока объявления"""
        try:
            # ID
            item_id = block.get("data-item-id", "")
            if not item_id:
                return None
            
            # Проверяем, не видели ли уже
            if self.db.is_seen(item_id):
                return None
            
            # Заголовок
            title_elem = block.select_one('a[data-marker="item-title"]') or block.select_one('h3')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Ссылка
            link_elem = title_elem if title_elem.name == 'a' else title_elem.find_parent('a')
            if not link_elem or 'href' not in link_elem.attrs:
                return None
            
            link = link_elem['href']
            if link.startswith('/'):
                link = f"https://www.avito.ru{link}"
            
            # Цена
            price = 0
            price_elem = block.select_one('meta[itemprop="price"]') or block.select_one('span[data-marker="item-price"]')
            if price_elem:
                if price_elem.name == 'meta':
                    price_text = price_elem.get('content', '0')
                else:
                    price_text = price_elem.get_text(strip=True)
                
                # Извлекаем цифры
                numbers = re.findall(r'\d+', price_text.replace(' ', ''))
                if numbers:
                    price = int(''.join(numbers))
            
            # Проверяем диапазон цен
            min_price = self.config['search']['min_price']
            max_price = self.config['search']['max_price']
            
            if not (min_price <= price <= max_price):
                return None
            
            # Проверяем, клиент ли это
            if not self.is_client(title):
                return None
            
            # Фото
            photo = None
            img_elem = block.select_one('img')
            if img_elem:
                photo = img_elem.get('src') or img_elem.get('data-src')
            
            return {
                'id': item_id,
                'city': city,
                'title': title,
                'price': price,
                'link': link,
                'photo': photo
            }
            
        except Exception as e:
            return None
    
    def process_items(self, items: List[Dict]):
        """Обработать найденные объявления"""
        for item in items:
            # Отправляем уведомление
            message = self._format_notification(item)
            if self.send_telegram(message):
                print(f"✅ Отправлено: {item['title'][:40]}...")
                
                # Сохраняем в базу
                self.db.add_seen_item(
                    item['id'], 
                    item['city'], 
                    item['title'], 
                    item['price']
                )
                
                self.stats["leads_found"] += 1
                
                # Обновляем статистику за сегодня
                self._update_daily_stats()
            
            # Пауза между отправками
            time.sleep(random.uniform(1, 3))
    
    def _format_notification(self, item: Dict) -> str:
        """Форматировать уведомление"""
        return f"""
<b>🚨 НОВЫЙ КЛИЕНТ • {item['city'].upper()}</b>

📄 <b>{item['title']}</b>
💰 <b>{item['price']:,} ₽</b>

🔗 <a href="{item['link']}">Открыть на Авито</a>

⚡ <b>Отвечай первым!</b>
📊 Всего найдено: {self.stats['leads_found']}
"""
    
    def _update_daily_stats(self):
        """Обновить дневную статистику"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(self.db.db_path)
            
            # Проверяем, есть ли запись на сегодня
            cursor = conn.execute("SELECT 1 FROM stats WHERE date = ?", (today,))
            if cursor.fetchone():
                conn.execute(
                    "UPDATE stats SET leads = leads + 1 WHERE date = ?",
                    (today,)
                )
            else:
                conn.execute(
                    "INSERT INTO stats (date, leads, scans) VALUES (?, 1, 1)",
                    (today,)
                )
            
            conn.commit()
            conn.close()
        except:
            pass
    
    def run_cycle(self):
        """Запустить один цикл проверки"""
        self.stats["current_cycle"] += 1
        cycle_num = self.stats["current_cycle"]
        
        print(f"\n🔄 Цикл #{cycle_num}")
        print("═" * 40)
        
        # Перемешиваем города
        cities = self.config['search']['cities'].copy()
        random.shuffle(cities)
        
        total_items = 0
        
        for city in cities:
            print(f"🔍 Проверяю {city}...")
            
            # Парсим город
            items = self.parse_city(city)
            total_items += len(items)
            
            # Обрабатываем найденные объявления
            if items:
                print(f"   Найдено {len(items)} объявлений, проверяю...")
                self.process_items(items)
            
            # Пауза между городами
            if city != cities[-1]:
                delay = random.uniform(*self.config['timing']['delay_between_cities'])
                time.sleep(delay)
        
        # Отчет о цикле
        print(f"\n📊 Цикл #{cycle_num} завершен")
        print(f"   Проверено городов: {len(cities)}")
        print(f"   Найдено объявлений: {total_items}")
        print(f"   Новых клиентов: {self.stats['leads_found']}")
        print(f"   Ошибок: {self.stats['errors']}")
        
        # Логируем
        self.db.log_event("INFO", f"Цикл #{cycle_num} завершен. Клиентов: {self.stats['leads_found']}")
    
    def start(self):
        """Запустить постоянную работу"""
        self.running = True
        
        # Приветственное сообщение
        welcome_msg = (
            f"🚀 <b>Avito Hunter запущен в Termux!</b>\n\n"
            f"📍 Города: {', '.join(self.config['search']['cities'])}\n"
            f"🔍 Поиск: {self.config['search']['query']}\n"
            f"💰 Цена: {self.config['search']['min_price']}-{self.config['search']['max_price']}₽"
        )
        self.send_telegram(welcome_msg)
        
        print("🚀 Парсер запущен! Нажмите Ctrl+C для остановки.")
        print("📱 Уведомления будут приходить в Telegram.")
        
        try:
            while self.running:
                # Запускаем цикл проверки
                self.run_cycle()
                
                # Пауза между циклами
                delay = random.uniform(*self.config['timing']['delay_between_cycles'])
                print(f"\n⏳ Следующая проверка через {int(delay/60)} минут...")
                
                # Разбиваем ожидание на части для возможности прерывания
                for _ in range(int(delay)):
                    if not self.running:
                        break
                    time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал остановки...")
        finally:
            self.stop()
    
    def stop(self):
        """Остановить работу"""
        self.running = False
        
        # Прощальное сообщение
        stats = self.db.get_stats()
        goodbye_msg = (
            f"🔴 <b>Avito Hunter остановлен</b>\n\n"
            f"📊 Итоги работы:\n"
            f"🔁 Циклов: {self.stats['current_cycle']}\n"
            f"🎯 Клиентов найдено: {self.stats['leads_found']}\n"
            f"💾 Всего в базе: {stats['total_seen']:,}\n"
            f"📈 Лидов сегодня: {stats['today_leads']}"
        )
        self.send_telegram(goodbye_msg)
        
        print("\n✅ Работа завершена!")
        print("📊 Статистика сохранена.")

# ────────────────────────────────────────────────
#  🎮 ГЛАВНОЕ МЕНЮ
# ────────────────────────────────────────────────
def main_menu():
    """Главное меню управления"""
    ui = TermuxUI()
    config_manager = ConfigManager()
    db = Database()
    
    while True:
        ui.clear()
        ui.banner()
        
        choice = ui.show_menu()
        
        if choice == "1":  # Запуск
            ui.clear()
            ui.banner()
            print("\n🚀 ЗАПУСК ПАРСЕРА")
            print("═" * 40)
            
            config = config_manager.load_config()
            hunter = AvitoHunter(config, db)
            
            # Показываем настройки
            print(f"📍 Города: {', '.join(config['search']['cities'])}")
            print(f"🔍 Запрос: {config['search']['query']}")
            print(f"💰 Цена: {config['search']['min_price']}-{config['search']['max_price']}₽")
            print(f"📱 Telegram: {config['telegram']['chat_id']}")
            
            print("\n" + "═" * 40)
            input("Нажмите Enter для запуска...")
            
            # Запускаем парсер
            try:
                hunter.start()
            except Exception as e:
                print(f"\n💥 Критическая ошибка: {e}")
                input("Нажмите Enter для возврата в меню...")
        
        elif choice == "2":  # Пауза
            print("\n⏸️  Функция приостановки в разработке")
            input("Нажмите Enter...")
        
        elif choice == "3":  # Перезагрузка
            print("\n🔄 Перезагрузка...")
            # В Termux просто перезапускаем скрипт
            os.execv(sys.executable, ['python'] + sys.argv)
        
        elif choice == "4":  # Настройки
            ui.clear()
            ui.banner()
            config = config_manager.edit_config_interactive()
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "5":  # Статистика
            ui.clear()
            ui.banner()
            print("\n📊 СТАТИСТИКА")
            print("═" * 40)
            
            stats = db.get_stats()
            print(f"👁️  Всего просмотрено: {stats['total_seen']:,}")
            print(f"🎯 Лидов всего: {stats['total_leads']}")
            print(f"📈 Лидов сегодня: {stats['today_leads']}")
            
            # Показываем последние 5 записей
            try:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.execute(
                    "SELECT title, city, created FROM seen_items ORDER BY created DESC LIMIT 5"
                )
                print(f"\n📝 Последние найденные:")
                for row in cursor.fetchall():
                    print(f"   • {row[0][:30]}... ({row[1]})")
                conn.close()
            except:
                pass
            
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "6":  # Логи
            ui.clear()
            ui.banner()
            print("\n📝 ЛОГИ")
            print("═" * 40)
            
            try:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.execute(
                    "SELECT timestamp, level, message FROM logs ORDER BY id DESC LIMIT 20"
                )
                
                for row in cursor.fetchall():
                    timestamp = row[0].split('.')[0] if '.' in row[0] else row[0]
                    level_icon = "✅" if row[1] == "INFO" else "⚠️ " if row[1] == "WARNING" else "❌"
                    print(f"{timestamp} {level_icon} {row[2][:50]}")
                
                conn.close()
            except Exception as e:
                print(f"Ошибка чтения логов: {e}")
            
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "7":  # Помощь
            ui.clear()
            ui.banner()
            print("\n🆘 ПОМОЩЬ")
            print("═" * 40)
            print("""
📱 **Avito Hunter для Termux**

**Основные функции:**
• Автоматический поиск клиентов на Avito
• Уведомления в Telegram
• Работа в фоновом режиме
• Статистика и логирование

**Установка:**
1. git clone https://github.com/ваш-репозиторий
2. cd avito-hunter-termux
3. python install.py

**Управление:**
• Запуск: python hunter.py
• В фоне: nohup python hunter.py &
• Остановка: pkill -f hunter.py

**Настройка:**
• Измените config.json или используйте меню
• Укажите свой Telegram токен и chat_id
            """)
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "8":  # Выход
            print("\n👋 До свидания!")
            break
        
        else:
            print("\n⚠️  Неверный выбор!")
            time.sleep(1)

# ────────────────────────────────────────────────
#  📦 УСТАНОВОЧНЫЙ СКРИПТ (install.py)
# ────────────────────────────────────────────────
def install_dependencies():
    """Установить зависимости"""
    print("📦 Установка зависимостей...")
    
    # Проверяем, есть ли pip
    try:
        import pip
    except ImportError:
        print("❌ PIP не установлен. Установите python и pip в Termux:")
        print("   pkg install python python-pip")
        return False
    
    # Устанавливаем зависимости
    dependencies = [
        "requests",
        "beautifulsoup4",
        "lxml"
    ]
    
    for package in dependencies:
        print(f"   Устанавливаю {package}...")
        os.system(f"pip install {package} --quiet")
    
    print("✅ Зависимости установлены!")
    return True

def setup_termux():
    """Настройка Termux"""
    print("⚙️  Настройка Termux...")
    
    # Разрешаем доступ к хранилищу
    if not os.path.exists("/data/data/com.termux"):
        print("⚠️  Скрипт запущен не в Termux!")
        return True
    
    # Создаем директории
    home = Path.home()
    (home / ".avito_hunter").mkdir(exist_ok=True)
    (home / "storage" / "shared" / "AvitoHunter").mkdir(parents=True, exist_ok=True)
    
    print("✅ Termux настроен!")
    return True

def create_shortcut():
    """Создать ярлык для быстрого запуска"""
    print("🔗 Создаю ярлыки...")
    
    home = Path.home()
    shortcut_content = """#!/data/data/com.termux/files/usr/bin/sh
cd ~/storage/shared/AvitoHunter
python hunter.py
"""
    
    # Создаем скрипт для быстрого запуска
    with open(home / "start-hunter.sh", "w") as f:
        f.write(shortcut_content)
    
    os.chmod(home / "start-hunter.sh", 0o755)
    
    print("✅ Ярлык создан: ~/start-hunter.sh")
    return True

# ────────────────────────────────────────────────
#  🚀 ТОЧКА ВХОДА
# ────────────────────────────────────────────────
if __name__ == "__main__":
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            # Режим установки
            TermuxUI.clear()
            TermuxUI.banner()
            print("\n🔧 РЕЖИМ УСТАНОВКИ")
            print("═" * 40)
            
            if setup_termux() and install_dependencies() and create_shortcut():
                print("\n🎉 Установка завершена успешно!")
                print("\n📌 Для запуска:")
                print("   python hunter.py")
                print("\n📌 Для быстрого запуска:")
                print("   ./start-hunter.sh")
            else:
                print("\n❌ Установка не удалась!")
            
            sys.exit(0)
    
    # Обычный запуск (меню)
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        input("Нажмите Enter для выхода...")
