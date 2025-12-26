#!/bin/bash

echo "=== Проверка статуса БД ==="
echo ""

# 1. Проверка статуса контейнера
echo "1. Статус контейнера PostgreSQL:"
docker compose ps db

echo ""
echo "2. Логи контейнера (последние 10 строк):"
docker compose logs --tail=10 db

echo ""
echo "3. Проверка подключения к БД:"
docker compose exec -T db pg_isready -U billing_user

echo ""
echo "4. Проверка существования базы данных:"
docker compose exec -T db psql -U billing_user -d billing_db -c "SELECT version();" 2>/dev/null && echo "✅ База данных доступна" || echo "❌ Не удалось подключиться к БД"

echo ""
echo "5. Список таблиц (если миграции применены):"
docker compose exec -T db psql -U billing_user -d billing_db -c "\dt" 2>/dev/null || echo "Таблицы еще не созданы"
