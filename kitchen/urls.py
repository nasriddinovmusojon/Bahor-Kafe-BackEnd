from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import KitchenTicketViewSet

router = DefaultRouter()
router.register(r"kitchen-tickets", KitchenTicketViewSet, basename="kitchen-tickets")

urlpatterns = [
    path("", include(router.urls)),
]