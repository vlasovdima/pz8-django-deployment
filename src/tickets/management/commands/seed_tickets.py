from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from tickets.models import Category, Ticket


class Command(BaseCommand):
    help = "Заполняет базу тестовыми категориями, пользователями и заявками для ПЗ №7."

    def handle(self, *args, **options):
        categories = [
            "Оборудование",
            "Программное обеспечение",
            "Сетевые сервисы",
            "Учебные материалы",
        ]
        cat_objs = {}
        for name in categories:
            obj, _ = Category.objects.get_or_create(name=name)
            cat_objs[name] = obj

        vlasov, created = User.objects.get_or_create(
            username="vlasov",
            defaults={
                "first_name": "Дмитрий",
                "last_name": "Власов",
                "email": "vlasov@mai.example.ru",
            },
        )
        if created:
            vlasov.set_password("StudentPass123!")
            vlasov.save()

        petrov, created = User.objects.get_or_create(
            username="petrov",
            defaults={
                "first_name": "Иван",
                "last_name": "Петров",
                "email": "petrov@mai.example.ru",
            },
        )
        if created:
            petrov.set_password("StudentPass123!")
            petrov.save()

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@mai.example.ru", "AdminPass123!")

        sample_tickets = [
            (
                vlasov,
                "Настройка сервера",
                "Проверить конфигурацию Nginx и открыть порт для тестового стенда.",
                cat_objs["Сетевые сервисы"],
                Ticket.Status.PROGRESS,
            ),
            (
                vlasov,
                "Обновление базы данных",
                "Применить миграции SQLite и проверить резервную копию.",
                cat_objs["Программное обеспечение"],
                Ticket.Status.NEW,
            ),
            (
                vlasov,
                "Проверка REST API",
                "Протестировать эндпоинты /api/tickets/ и /api/categories/ после деплоя.",
                cat_objs["Программное обеспечение"],
                Ticket.Status.DONE,
            ),
            (
                vlasov,
                "Замена кабеля в аудитории 317",
                "Не работает розетка Ethernet на третьем рабочем месте.",
                cat_objs["Оборудование"],
                Ticket.Status.NEW,
            ),
            (
                petrov,
                "Чужая заявка Петрова",
                "Не должна быть доступна пользователю vlasov через API.",
                cat_objs["Оборудование"],
                Ticket.Status.NEW,
            ),
        ]

        for owner, title, desc, cat, status in sample_tickets:
            Ticket.objects.get_or_create(
                owner=owner,
                title=title,
                defaults={
                    "description": desc,
                    "category": cat,
                    "status": status,
                },
            )

        self.stdout.write(self.style.SUCCESS("Тестовые категории и заявки успешно добавлены."))
