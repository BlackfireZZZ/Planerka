# Сервис бэкенда

Приложение на FastAPI, которое обеспечивает работу платформы расписаний. Предоставляет REST API, управляет схемой PostgreSQL и обрабатывает загрузки в S3-совместимое хранилище (по умолчанию MinIO).

## Стек технологий
- FastAPI + Uvicorn (ASGI-сервер)
- SQLAlchemy 2.0 (async) с asyncpg
- Alembic для миграций БД
- aioboto3 для доступа к S3/MinIO
- uv для управления зависимостями и скриптов

## Требования
- Python 3.13 (управляется через `uv`)
- PostgreSQL 15+ (Docker Compose использует 18-alpine)
- MinIO или любое S3-совместимое хранилище для загрузки файлов
- Docker и Docker Compose v2 (опционально, но рекомендуется для согласованности)

## Быстрый старт

### Запуск в Docker Compose (рекомендуется)
```bash
cd ..
docker compose up --build backend db minio
```
Контейнер бэкенда выполняет `scripts/init.sh`, который ждёт PostgreSQL, применяет миграции Alembic и затем запускает Uvicorn на порту 8000.

### Локальный запуск с uv
```bash
cd backend
uv sync
touch .env  # заполните переменные, перечисленные ниже
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```
Запустите PostgreSQL и MinIO локально (Docker, Podman или предпочитаемый вами способ) и убедитесь, что значения в `.env` указывают на эти сервисы.

## Переменные окружения

| Переменная | По умолчанию | Описание |
| --- | --- | --- |
| `APP_NAME` | FastAPI Base App | Название в OpenAPI |
| `APP_VERSION` | 1.0.0 | Семантическая версия в документации |
| `DEBUG` | true | Подробный SQL-логирование |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | `db`, `5432`, `postgres`, `postgres`, `postgres` | Параметры подключения к PostgreSQL |
| `S3_ENDPOINT_URL` | http://minio:9000 | Endpoint MinIO |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | minioadmin / minioadmin | Учётные данные MinIO |
| `S3_REGION` | us-east-1 | Фиктивный регион для локального MinIO |
| `S3_BUCKET_NAME` | default-bucket | Бакет создаётся автоматически при старте |
| `S3_USE_SSL` | false | Установите true для AWS S3 |

Поместите значения в `.env` в корне backend; `pydantic-settings` загружает их автоматически.

## Структура проекта
```
backend/
├── app/
│   ├── api/routes/ping.py        # Endpoint проверки состояния
│   ├── core/config.py            # Настройки и разбор env
│   ├── db/                       # Модели и сессии SQLAlchemy
│   └── storage/s3.py             # Вспомогательные функции MinIO/S3
├── alembic/                      # Скрипты миграций
├── scripts/                      # Точка входа и вспомогательные скрипты
├── tests/                        # Набор тестов Pytest
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Частые команды
- `uv sync` — установка/обновление зависимостей из `pyproject.toml`
- `uv run uvicorn app.main:app --reload` — запуск API локально
- `uv run alembic revision --autogenerate -m "message"` — создание миграции
- `uv run alembic upgrade head` — применение миграций
- `uv run pytest` — выполнение тестов бэкенда

## Миграции базы данных
Alembic настроен на использование синхронного URL БД из `settings.DATABASE_URL_SYNC`.
1. Внесите изменения в модели.
2. Создайте миграцию: `uv run alembic revision --autogenerate -m "add_teacher_subject"`.
3. Примените локально: `uv run alembic upgrade head`.
4. При запуске в Docker `scripts/init.sh` вызывает `scripts/migrate.sh`, поэтому миграции выполняются автоматически при старте контейнера.

## Тестирование
Запуск лёгкого набора тестов (сейчас в основном smoke-тесты):
```bash
uv run pytest -q
```
Добавляйте новые тесты в `tests/` и делайте их детерминированными, чтобы они стабильно выполнялись в CI и Docker.

## API
| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/ping` | Проверка состояния с проверкой подключения к БД и возвратом версии PostgreSQL. |

Будущие эндпоинты для расписаний будут в `app/api/v1` после реализации.

## Заметки по хранилищу
- `app.storage.s3.S3Storage` при старте проверяет наличие настроенного бакета и предоставляет вспомогательные функции для загрузки, выгрузки и удаления объектов.
- Для AWS S3 укажите `S3_ENDPOINT_URL=https://s3.amazonaws.com` и `S3_USE_SSL=true` и задайте учётные данные IAM через переменные окружения.

## Устранение неполадок
- **Ошибка подключения к БД**: проверьте доступность PostgreSQL и совпадение учётных данных с `.env`.
- **Ошибки бакета**: удалите локальный том MinIO (`docker volume rm cs-project-2025-chessnok_minio_data`), если состояние бакета стало некорректным.
- **Расхождение зависимостей**: выполните `uv sync` заново после изменений в `pyproject.toml` или после подтягивания новых изменений.
