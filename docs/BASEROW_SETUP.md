# Скрипт автоматической настройки Baserow

Этот скрипт автоматически создаст все необходимые таблицы и поля в вашей базе данных Baserow.

## Быстрый старт

### 1. Создайте пустую базу в Baserow

1. Зайдите на [baserow.io](https://baserow.io)
2. Создайте новую базу данных (не создавайте таблицы вручную!)
3. Скопируйте **Database ID** из URL
4. Сгенерируйте **API Token** в настройках профиля

### 2. Запустите скрипт

#### Вариант A: Локально

```bash
# Установите переменные окружения
export BASEROW_TOKEN="your_token_here"
export BASEROW_DATABASE_ID="your_database_id_here"

# Запустите скрипт
python setup_baserow_db.py
```

#### Вариант B: Через файл .env

```bash
# Создайте файл .env
cp .env.example .env

# Отредактируйте .env, добавив:
# BASEROW_TOKEN=your_token_here
# BASEROW_DATABASE_ID=your_database_id_here

# Запустите скрипт
python setup_baserow_db.py
```

#### Вариант C: Автоматически через GitHub Actions

При первом запуске workflow в GitHub Actions скрипт выполнится автоматически.

## Что будет создано

Скрипт создаст 7 таблиц со следующими полями:

### 1. keywords
- `keyword` (text, обязательное)
- `volume` (number)
- `competition` (text)
- `category` (text)
- `created_at` (date)
- `updated_at` (date)

### 2. trends
- `trend_name` (text, обязательное)
- `growth_rate` (number)
- `category` (text)
- `description` (text)
- `detected_at` (date)

### 3. pins
- `pin_id` (text, обязательное)
- `image_url` (url)
- `description` (text)
- `link` (url)
- `board_name` (text)
- `created_at` (date)

### 4. engagement
- `pin_id` (text, обязательное)
- `saves` (number)
- `clicks` (number)
- `impressions` (number)
- `engagement_rate` (number)
- `recorded_at` (date)

### 5. agent_log
- `timestamp` (date, обязательное)
- `action` (text)
- `status` (text)
- `message` (text)
- `details` (text)

### 6. scraper_health
- `check_time` (date, обязательное)
- `cpu_usage` (number)
- `memory_usage` (number)
- `status` (text)
- `uptime_hours` (number)
- `last_error` (text)

### 7. diagnostic_reports
- `report_date` (date, обязательное)
- `issues_found` (number)
- `recommendations` (text)
- `summary` (text)
- `severity` (text)

## Проверка результата

После выполнения скрипта:

1. Зайдите в вашу базу данных на baserow.io
2. Вы должны увидеть 7 новых таблиц
3. Каждая таблица содержит соответствующие поля

## Повторный запуск

Скрипт можно запускать многократно - он проверит существующие таблицы и поля, и создаст только недостающие.

## Требования

- Python 3.11+
- Установленные зависимости: `pip install -r requirements.txt`
- Действительный токен Baserow с правами на запись

## Troubleshooting

### Ошибка "Invalid token"
Проверьте, что токен скопирован полностью и без лишних пробелов

### Ошибка "Database not found"
Убедитесь, что Database ID указан верно (это число из URL после `/database/`)

### Ошибка прав доступа
Токен должен иметь права на создание таблиц в базе данных
