```markdown
# 🚀 Avito Hunter PRO для Termux

Автоматический поиск клиентов на Avito с уведомлениями в Telegram.

## 📱 Установка в Termux

### Быстрая установка (одной командой):

```bash
# 1. Клонируем репозиторий
cd ~/storage/shared
git clone https://github.com/ваш-никнейм/avito-hunter-termux.git AvitoHunter
cd AvitoHunter

# 2. Запускаем установку
bash install.sh
```

Ручная установка:

```bash
# 1. Обновляем Termux
pkg update && pkg upgrade

# 2. Устанавливаем Python
pkg install python python-pip

# 3. Устанавливаем зависимости
pip install requests beautifulsoup4 lxml

# 4. Даем доступ к хранилищу
termux-setup-storage

# 5. Копируем файлы
mkdir -p ~/storage/shared/AvitoHunter
cp *.py ~/storage/shared/AvitoHunter/
cd ~/storage/shared/AvitoHunter

# 6. Запускаем установку
python hunter.py install
```
