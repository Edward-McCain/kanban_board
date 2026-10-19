# Полотно

Доска веб-команды: колонки, карточки, перенос между колонками.

## Локально

Postgres уже должен слушать `127.0.0.1:5432`, база `polotno`. Из этой папки:

```bash
uv sync
uv run alembic upgrade head
SEED_BOARD=1 uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Интерфейс, вторым процессом:

```bash
cd web
npm install
npm run dev
```

Доска открывается на http://127.0.0.1:5173. Описание API — на http://127.0.0.1:8000/docs.

`SEED_BOARD=1` заполняет пустую доску учебными карточками. Повторный запуск ничего не добавляет, если колонки уже есть.

## Docker

Postgres в контейнере публикуется на `5433`, чтобы не задеть локальный `5432`.

```bash
docker compose up --build
```

Доска и API — на http://127.0.0.1:8000. Пароль базы в compose: `polotno`.

## Проверка

```bash
uv run pytest
uv run ruff check app tests alembic
uv run mypy
```
