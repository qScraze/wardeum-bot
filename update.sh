#!/bin/bash
echo "=== Шаг 1: Получение изменений из репозитория ==="
git pull origin main

echo "=== Шаг 2: Сборка фронтенда ==="
docker compose run --rm frontend-builder

echo "=== Шаг 3: Пересборка и запуск контейнеров ==="
docker compose up -d --build

echo "=== Шаг 4: Вывод URL-адреса туннеля Cloudflare ==="
sleep 3
docker compose logs tunnel | grep -o 'https://.*trycloudflare.com' | tail -n 1

echo "=== Готово! ==="
