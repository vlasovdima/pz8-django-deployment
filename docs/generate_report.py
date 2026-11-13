import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = Path(r"c:\Users\kirak\Downloads\mp\.agents\skills\gost-student-reports\scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))

from gost_docx import GostReport


def build_report():
    rep = GostReport(base_dir=str(BASE_DIR), screenshots_dir=str(BASE_DIR / "screenshots"))

    # Страница 1: Титульный лист
    rep.title_page(
        work_type="Практическое занятие № 8",
        work_subtitle="по дисциплине «Технологии разработки веб-приложений»",
        discipline="",
        topic="«Подготовка Django-приложения к развёртыванию, настройка серверного окружения и публикация на облачной платформе»",
        student_name="Власов Дмитрий",
        student_group="М3О-236БВ-25",
        teacher_name="Александрова С.С.",
        year="2026",
    )

    # Страница 2: Содержание
    rep.toc([
        ("1 Архитектура и состав компонентов развёртывания", 3),
        ("2 Конфигурация окружения, зависимости и сборка проекта", 4),
        ("3 Endpoint /healthz/, обработка недоступности API и разбор ошибок", 6),
        ("4 Локальная проверка при DEBUG=False и подготовка к Render", 7),
        ("5 Ответы на контрольные вопросы", 9),
        ("Заключение", 11),
        ("Список использованных источников", 12),
    ])

    # Раздел 1
    rep.heading("1 Архитектура и состав компонентов развёртывания", level=1)
    rep.para(
        "В этой работе я подготовил Django-приложение управления заявками из ПЗ №7 к запуску вне локальной среды разработки. "
        "Обычный сервер runserver подходит только для отладки на своём компьютере: он однопоточный, не держит высокую нагрузку и не предназначен для открытого интернета. "
        "Чтобы проект нормально работал на облачной платформе Render, я перевёл настройки на переменные окружения, подключил раздачу статики через WhiteNoise и подготовил конфигурацию под WSGI-сервер Gunicorn и базу PostgreSQL."
    )

    rep.diagram(
        "Схема инфраструктуры развёрнутого веб-приложения",
        "Браузер пользователя\n"
        "        │  HTTPS\n"
        "        ▼\n"
        "Облачный прокси Render\n"
        "        │  HTTP (X-Forwarded-Proto: https)\n"
        "        ▼\n"
        "Gunicorn (WSGI-сервер, --bind 0.0.0.0:$PORT)\n"
        "        │\n"
        "        ├──► WhiteNoiseMiddleware (выдача статики из STATIC_ROOT)\n"
        "        └──► Django / DRF (страницы, /healthz/, /api/tickets/, /api/categories/)\n"
        "                    │\n"
        "                    ▼  DATABASE_URL (psycopg)\n"
        "             PostgreSQL (постоянное хранение данных)",
    )

    rep.table(
        "Компоненты серверного окружения и их назначение",
        ["Компонент", "Пакет / сервис", "Назначение в проекте"],
        [
            ["Веб-хостинг", "Render Web Service", "Запуск Python-процесса и публикация сайта по HTTPS"],
            ["WSGI-сервер", "gunicorn 27.0.1", "Обработка HTTP-запросов к Django на Linux"],
            ["Фреймворк и API", "Django 6.1.2, DRF 3.18.3", "Маршрутизация, HTML-шаблоны, сессии и REST API"],
            ["Статические файлы", "whitenoise 6.12.0", "Раздача собранных CSS и JS при DEBUG=False"],
            ["База данных", "PostgreSQL + dj-database-url + psycopg", "Постоянное хранение пользователей, категорий и заявок"],
            ["Конфигурация", "Переменные окружения (.env.example)", "Передача SECRET_KEY, DEBUG, ALLOWED_HOSTS и DATABASE_URL без утечки в Git"],
        ],
    )

    # Раздел 2
    rep.heading("2 Конфигурация окружения, зависимости и сборка проекта", level=1)
    rep.para(
        "Сначала я скопировал исходный проект из ПЗ №7 в отдельную папку и доустановил пакеты, нужные для продакшена: gunicorn, whitenoise, dj-database-url и psycopg[binary]. "
        "Список зависимостей я сохранил в файле src/requirements.txt, включив туда только те библиотеки, которые реально использует приложение, чтобы на Linux-сервере Render не ставились лишние локальные пакеты."
    )
    rep.para(
        "Дальше я переписал src/config/settings.py. Жестко прописанный SECRET_KEY и DEBUG=True из кода убрал: теперь ключ читается из DJANGO_SECRET_KEY, а если переменная не задана, Django сразу выбрасывает ImproperlyConfigured. "
        "Для ALLOWED_HOSTS и CSRF_TRUSTED_ORIGINS добавил разбор списков через запятую. Подключение к базе настроил через dj_database_url.config с резервным SQLite для локальных тестов и параметрами conn_max_age=600 и conn_health_checks=True."
    )

    rep.listing(
        "Фрагмент настроек безопасности, БД и статики в src/config/settings.py",
        'SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")\n'
        'if not SECRET_KEY:\n'
        '    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY")\n\n'
        'DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"\n\n'
        'ALLOWED_HOSTS = [\n'
        '    host.strip()\n'
        '    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")\n'
        '    if host.strip()\n'
        ']\n\n'
        'DATABASES = {\n'
        '    "default": dj_database_url.config(\n'
        '        default=f"sqlite:///{BASE_DIR / \'db.sqlite3\'}",\n'
        '        conn_max_age=600,\n'
        '        conn_health_checks=True,\n'
        '    )\n'
        '}\n\n'
        'STATIC_URL = "static/"\n'
        'STATIC_ROOT = BASE_DIR / "staticfiles"\n'
        'STORAGES = {\n'
        '    "staticfiles": {\n'
        '        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",\n'
        '    }\n'
        '}\n'
        'SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")',
    )

    rep.para(
        "Чтобы не залить в репозиторий пароли и локальную базу, я проверил .gitignore (туда уже входят .env, *.sqlite3, staticfiles/, .venv/ и __pycache__/) и создал шаблон .env.example с именами переменных без секретных значений. "
        "Для автоматической сборки на Render подготовил скрипт src/build.sh, который обновляет pip, ставит зависимости из requirements.txt и запускает collectstatic."
    )

    rep.listing(
        "Сценарий сборки src/build.sh и шаблон переменных .env.example",
        "# src/build.sh\n"
        "#!/usr/bin/env bash\n"
        "set -e\n"
        "python -m pip install --upgrade pip\n"
        "python -m pip install -r requirements.txt\n"
        "python manage.py collectstatic --noinput\n\n"
        "# .env.example\n"
        "DJANGO_SECRET_KEY=replace-with-a-strong-random-value\n"
        "DJANGO_DEBUG=False\n"
        "DJANGO_ALLOWED_HOSTS=your-app.onrender.com\n"
        "DJANGO_CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com\n"
        "DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME",
    )

    # Раздел 3
    rep.heading("3 Endpoint /healthz/, обработка недоступности API и разбор ошибок", level=1)
    rep.para(
        "По заданию я добавил в src/config/urls.py маршрут /healthz/, который возвращает простой JSON {\"status\": \"ok\"} со статусом HTTP 200. "
        "Он не раскрывает версии пакетов, переменные окружения или данные пользователей, но позволяет платформе быстро понять, что процесс Django запущен. "
        "При этом сам /healthz/ к базе не обращается: реальную связь с БД подтверждает запрос GET /api/categories/ или загрузка списка заявок через GET /api/tickets/."
    )
    rep.para(
        "Также я доработал функцию apiRequest в файле src/tickets/static/tickets/app.js. Раньше при обрыве сети браузер падал с необработанным исключением TypeError, а при ошибке 500 без JSON выводил общую фразу. "
        "Теперь вызов fetch обёрнут в try/catch: если сервер не отвечает, пользователь видит понятное сообщение «Сервис API временно недоступен. Проверьте подключение к сети или попробуйте обновить страницу позже.»."
    )
    rep.para(
        "При первом запуске команд проверки я столкнулся сразу с двумя реальными проблемами конфигурации. "
        "Во-первых, команда collectstatic упала на файле vendor/tabler/css/tabler.min.css: хранилище CompressedManifestStaticFilesStorage требовало отсутствующий файл tabler.min.css.map, ссылка на который была в комментарии минифицированного CSS. "
        "Я заменил бэкенд на CompressedStaticFilesStorage, после чего сборка статики прошла без ошибок (обработано 156 файлов). "
        "Во-вторых, команда check --deploy выдала ошибку mail.E001 из-за консольного бэкенда почты при DEBUG=False, а в приложении tickets не было папки migrations. Я переключил MAILERS на SMTP при DEBUG=False и создал начальную миграцию tickets/migrations/0001_initial.py."
    )

    rep.table(
        "Устранённые ошибки конфигурации при подготовке к развёртыванию",
        ["Симптом / ошибка", "Причина", "Как исправлено"],
        [
            [
                "CommandError: vendor/tabler/css/tabler.min.css.map could not be found",
                "CompressedManifestStaticFilesStorage падает при отсутствии .map-файла, указанного в vendor CSS",
                "Заменил бэкенд статики в STORAGES на whitenoise.storage.CompressedStaticFilesStorage",
            ],
            [
                "SystemCheckError: (mail.E001) console.EmailBackend при check --deploy",
                "В настройках был жёстко задан консольный бэкенд почты даже для DEBUG=False",
                "Разделил настройку MAILERS по флагу DEBUG: консоль для разработки, SMTP для эксплуатации",
            ],
            [
                "Отсутствовала папка migrations в приложении tickets",
                "В заготовке ПЗ №7 не были сгенерированы файлы миграций для Category и Ticket",
                "Выполнил python manage.py makemigrations tickets и применил migrate",
            ],
        ],
    )

    # Раздел 4
    rep.heading("4 Локальная проверка при DEBUG=False и подготовка к Render", level=1)
    rep.para(
        "Перед публикацией я проверил работу проекта локально в режиме DEBUG=False с временными переменными окружения в PowerShell. "
        "Запустил python manage.py check, python manage.py collectstatic --noinput, python manage.py check --deploy (ошибок нет, остались только ожидаемые предупреждения про HTTPS-редирект для локального HTTP-теста) и python manage.py migrate. "
        "После этого написал автоматический тест tests/test_all.py, который проверил 7 сценариев: ответ /healthz/, блокировку чужого Host-заголовка (HTTP 400 DisallowedHost), раздачу статики через WhiteNoise, защиту API без входа (HTTP 403), создание заявки (POST /api/tickets/), отклонение неверного перехода статуса new -> done (HTTP 400) и изоляцию чужих заявок (HTTP 404). Все 7 проверок прошли успешно."
    )

    rep.figure("1_healthz.png", "Проверка работы маршрута /healthz/ при DEBUG=False")
    rep.figure("2_login.png", "Страница входа в систему со стилями Tabler через WhiteNoise")
    rep.figure("3_tickets_dashboard.png", "Интерфейс управления заявками после авторизации")
    rep.figure("4_api_categories.png", "Ответ REST API /api/categories/ с категориями из базы данных")

    rep.para(
        "Для развёртывания на облачной платформе Render подготовлены все файлы: src/requirements.txt, src/build.sh, .env.example и подробная инструкция в README.md. "
        "На Render нужно создать бесплатную базу данных Postgres (pz8-django-db) и Web Service с Root Directory = src, Build Command = bash build.sh и Start Command = gunicorn config.wsgi:application --bind 0.0.0.0:$PORT, а затем задать пять переменных окружения и выполнить python manage.py migrate и seed_tickets в консоли сервиса."
    )

    rep.github_repo_note("https://github.com/vlasovdima/pz8-django-deployment")

    # Раздел 5
    rep.heading("5 Ответы на контрольные вопросы", level=1)
    rep.bullets([
        "Отличие runserver от Gunicorn: runserver — встроенный однопоточный сервер разработки Django без защиты от нагрузки и параллельных соединений. Gunicorn — боевой многопроцессный WSGI-сервер для Linux, который умеет управлять воркерами, таймаутами и перезапуском процессов.",
        "Назначение ALLOWED_HOSTS: список разрешённых доменных имён в заголовке Host. Защищает приложение от HTTP Host Header атак и подмены ссылок, при DEBUG=False несоответствующий запрос сразу отклоняется с кодом 400.",
        "Почему DEBUG=False обязателен: при DEBUG=True Django показывает подробный traceback с локальными переменными, настройками и SQL-запросами любому пользователю при ошибке, что приводит к утечке секретов и структуры проекта.",
        "Отличие STATIC_ROOT от STATIC_URL: STATIC_URL задаёт URL-префикс, по которому браузер запрашивает стили и скрипты (/static/). STATIC_ROOT — физическая папка на диске (staticfiles), куда команда collectstatic собирает все файлы перед запуском WhiteNoise.",
        "Почему SQLite на временном диске не сохраняет данные: файловая система бесплатных контейнеров Render эфемерная. При каждом перезапуске или новом деплое диск пересоздаётся с нуля, поэтому локальный файл db.sqlite3 стирается, в отличие от отдельного сервиса PostgreSQL.",
        "Какой HTTP-запрос подтверждает реальную связь с БД: GET /api/categories/ или GET /api/tickets/ после авторизации, так как они выполняют реальный SQL-запрос SELECT к таблицам PostgreSQL, в отличие от /healthz/.",
    ])

    # Заключение
    rep.heading("Заключение", level=1)
    rep.para(
        "В ходе практического занятия я подготовил проект управления заявками из ПЗ №7 к промышленной эксплуатации. "
        "Настройки перенесены в переменные окружения, настроена сборка и выдача статики через WhiteNoise, добавлен маршрут /healthz/ и понятное уведомление при недоступности API. "
        "Сложнее всего было разобраться с падением collectstatic на отсутствующем source map у Tabler и с отсутствием миграций в приложении tickets. После исправления этих проблем локальная проверка при DEBUG=False и все 7 автотестов прошли без единой ошибки."
    )

    # Список источников
    rep.sources([
        "Django Documentation. How to deploy Django [Электронный ресурс]. – URL: https://docs.djangoproject.com/en/6.1/howto/deployment/ (дата обращения: 13.11.2026).",
        "Render Documentation. Deploy a Django App [Электронный ресурс]. – URL: https://render.com/docs/deploy-django (дата обращения: 13.11.2026).",
        "WhiteNoise Documentation. Static File Serving for Python Web Apps [Электронный ресурс]. – URL: https://whitenoise.readthedocs.io/ (дата обращения: 13.11.2026).",
        "Gunicorn Documentation. Python WSGI HTTP Server for UNIX [Электронный ресурс]. – URL: https://docs.gunicorn.org/ (дата обращения: 13.11.2026).",
    ])

    out_in_docs = BASE_DIR / "docs" / "Отчет_ПЗ8_Власов_М3О-236БВ-25.docx"
    out_in_root = Path(r"c:\Users\kirak\Downloads\mp\Отчет_ПЗ8_Власов_М3О-236БВ-25.docx")
    rep.save(str(out_in_docs))
    shutil.copy2(out_in_docs, out_in_root)
    print(f"Report saved to:\n  {out_in_docs}\n  {out_in_root}")


if __name__ == "__main__":
    build_report()
