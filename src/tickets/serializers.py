from rest_framework import serializers
from .models import Category, Ticket


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")


class TicketSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "title",
            "description",
            "category",
            "category_name",
            "status",
            "status_display",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate_title(self, value):
        # Убираем лишние пробелы по краям, чтобы "     " не прошло проверку длины
        clean_title = value.strip()
        if len(clean_title) < 5:
            raise serializers.ValidationError(
                "Название заявки должно содержать не менее 5 символов."
            )
        return clean_title

    def validate(self, attrs):
        # При создании новая заявка всегда должна стартовать со статуса "Новая"
        if self.instance is None:
            if attrs.get("status", Ticket.Status.NEW) != Ticket.Status.NEW:
                raise serializers.ValidationError(
                    {"status": "Новая заявка должна иметь статус «Новая»."}
                )
            return attrs

        old_status = self.instance.status
        new_status = attrs.get("status", old_status)

        # Разрешённые переходы строго по цепочке: Новая -> В работе -> Выполнена
        allowed = {
            Ticket.Status.NEW: {Ticket.Status.PROGRESS},
            Ticket.Status.PROGRESS: {Ticket.Status.DONE},
            Ticket.Status.DONE: set(),
        }

        if new_status != old_status and new_status not in allowed[old_status]:
            raise serializers.ValidationError(
                {"status": "Недопустимый переход статуса. Доступна только последовательная смена: Новая -> В работе -> Выполнена."}
            )
        return attrs
