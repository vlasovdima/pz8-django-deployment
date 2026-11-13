from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, TicketViewSet, dashboard

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("tickets", TicketViewSet, basename="tickets")

urlpatterns = [
    path("tickets/", dashboard, name="tickets_dashboard"),
    path("api/", include(router.urls)),
]
