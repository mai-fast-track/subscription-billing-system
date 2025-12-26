#!/bin/bash
set -e

echo "Быстрая установка на macOS через brew"
echo ""

# Установка Colima + Docker
if ! command -v docker &> /dev/null; then
    echo "Установка Docker..."
    arch -arm64 brew install docker docker-compose colima
fi

# Запуск Colima
if ! colima status &> /dev/null; then
    echo "Запуск Colima..."
    colima start
fi

# Проверка что Docker работает
if ! docker ps &> /dev/null; then
    echo "Docker не запущен"
    exit 1
fi

# Создание .env если нет
if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
fi

# Остановка старых контейнеров
docker compose down 2>/dev/null || true

# Запуск приложения
echo "Запуск приложения"
docker compose up --build -d

sleep 3

# Проверка
if docker compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Готово!"
    echo "🌐 http://localhost:8000"
    echo "📚 http://localhost:8000/docs"
else
    echo "Ошибка. Смотрите логи: docker compose logs"
    exit 1
fi
