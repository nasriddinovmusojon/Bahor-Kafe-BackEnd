from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet,CheckSettingsViewSet,TaxSettingsViewSet,OrderFlowSettingsViewSet,RestaurantSettingsViewSet

router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branches'),
router.register(r'check-settings', CheckSettingsViewSet, basename='check-settings'),
router.register(r'tax-settings', TaxSettingsViewSet, basename='tax-settings'),
router.register(r'settings', OrderFlowSettingsViewSet, basename='settings'),
router.register(r'restaurant-settings', RestaurantSettingsViewSet, basename='restaurant-settings')


urlpatterns = [
    path('', include(router.urls)),
]