from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Category, Ticket
from .serializers import CategorySerializer, TicketSerializer


@login_required
@ensure_csrf_cookie
def dashboard(request):
    """Отображает страницу управления заявками; данные подгружаются через REST API."""
    return render(request, "tickets/dashboard.html")


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свои заявки — чужие вернут 404
        queryset = Ticket.objects.filter(
            owner=self.request.user
        ).select_related("category")

        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        # Владельца задаём на сервере из текущей сессии, а не из тела запроса
        serializer.save(owner=self.request.user)
