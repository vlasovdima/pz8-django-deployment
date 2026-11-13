from django.conf import settings
from django.db import models


# Справочник категорий заявок (Оборудование, ПО, Сетевые сервисы и т.д.)
class Category(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


# Основная сущность заявки, привязанная к категории и автору
class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        PROGRESS = "progress", "В работе"
        DONE = "done", "Выполнена"

    title = models.CharField("Заголовок", max_length=200)
    description = models.TextField("Описание", blank=True)
    # PROTECT не даёт удалить категорию, пока на неё ссылаются заявки
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Категория",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name="Автор",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
