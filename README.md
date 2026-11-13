# ПЗ №8. Подготовка и развёртывание Django-приложения (Render + PostgreSQL + Gunicorn + WhiteNoise)

Репозиторий проекта: [https://github.com/vlasovdima/pz8-django-deployment](https://github.com/vlasovdima/pz8-django-deployment)

## Архитектура

`Браузер пользователя → HTTPS → Render Web Service → Gunicorn → Django / DRF → PostgreSQL`

- **Gunicorn** — WSGI-сервер для запуска Django на Linux (`gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`).
- **WhiteNoise** — раздача собранных статических файлов (`collectstatic`) при `DEBUG=False`.
- **dj-database-url + psycopg[binary]** — подключение к PostgreSQL через `DATABASE_URL` с `conn_max_age=600` и `conn_health_checks=True`.
- **Переменные окружения** — `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`.

## Локальная проверка в режиме эксплуатации (PowerShell)

```powershell
cd src
$env:DJANGO_SECRET_KEY = "replace-with-a-long-random-secret-key"
$env:DJANGO_DEBUG = "False"
$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost"
$env:DJANGO_CSRF_TRUSTED_ORIGINS = "http://127.0.0.1:8000,http://localhost:8000"

python manage.py check
python manage.py collectstatic --noinput
python manage.py check --deploy
python manage.py migrate
python manage.py seed_tickets
python manage.py runserver
```

Проверка доступности:
- `GET /healthz/` → `{"status": "ok"}` (HTTP 200)
- `GET /tickets/` → интерфейс управления заявками (после входа)
- `GET /api/categories/` → категории из базы данных

## Развёртывание на Render

1. Создать сервис **Postgres** (`pz8-django-db`, тариф Free, регион Oregon / Frankfurt).
2. Создать **Web Service**:
   - **Root Directory**: `src`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
3. В разделе **Environment Variables** задать:
   - `DATABASE_URL` — `Internal Database URL` из созданного Postgres
   - `DJANGO_SECRET_KEY` — сгенерированный случайный ключ
   - `DJANGO_DEBUG` — `False`
   - `DJANGO_ALLOWED_HOSTS` — `<your-app>.onrender.com`
   - `DJANGO_CSRF_TRUSTED_ORIGINS` — `https://<your-app>.onrender.com`
4. После первого запуска выполнить миграции и заполнение справочников в Shell:
   ```bash
   python manage.py migrate
   python manage.py seed_tickets
   ```
