```bash
#!/data/data/com.termux/files/usr/bin/bash
# Установочный скрипт для Termux

echo "🔧 Установка Avito Hunter для Termux"
echo "====================================="

# Обновление пакетов
echo "📦 Обновление пакетов..."
pkg update -y && pkg upgrade -y

# Установка Python
echo "🐍 Установка Python..."
pkg install python python-pip -y

# Установка зависимостей
echo "📚 Установка зависимостей..."
pip install requests beautifulsoup4 lxml

# Разрешение на доступ к хранилищу
echo "📁 Настройка доступа к хранилищу..."
termux-setup-storage
sleep 2

# Создание директорий
echo "📂 Создание директорий..."
mkdir -p ~/storage/shared/AvitoHunter
mkdir -p ~/.avito_hunter

# Копирование файлов
echo "📄 Копирование файлов..."
cp hunter.py ~/storage/shared/AvitoHunter/
cp requirements.txt ~/storage/shared/AvitoHunter/

# Создание ярлыка
echo "🔗 Создание ярлыка..."
cat > ~/start-avito-hunter.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/storage/shared/AvitoHunter
python hunter.py
EOF

chmod +x ~/start-avito-hunter.sh

# Создание автозапуска
echo "⚙️ Настройка автозапуска..."
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/avito-hunter << 'EOF'
#!/data/data/com.termux/files/usr/bin/sh
sleep 10
cd /data/data/com.termux/files/home/storage/shared/AvitoHunter
nohup python hunter.py > hunter.log 2>&1 &
EOF

chmod +x ~/.termux/boot/avito-hunter

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "📌 Команды для запуска:"
echo "   Обычный запуск:  ./start-avito-hunter.sh"
echo "   Фоновый запуск:  nohup python hunter.py &"
echo "   Просмотр логов:  tail -f hunter.log"
echo "   Остановка:       pkill -f hunter.py"
echo ""
echo "📱 После перезагрузки Termux скрипт запустится автоматически!"
echo ""
```
