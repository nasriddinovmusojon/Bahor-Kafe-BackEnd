from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import (
    EmployeeViewSet,
    LoginAPIView,
    SetPinAPIView,
    PinLoginAPIView,
    MeAPIView,
    LogoutAPIView,
    EmployeePermissionAPIView
)

router = DefaultRouter()
router.register(r"employees", EmployeeViewSet, basename="employees")

urlpatterns = [
    path("", include(router.urls)),

    path("auth/login/", LoginAPIView.as_view(), name="employee-login"),
    path("auth/pin-login/", PinLoginAPIView.as_view(), name="employee-pin-login"),
    path("auth/set-pin/", SetPinAPIView.as_view(), name="employee-set-pin"),
    path("auth/me/", MeAPIView.as_view(), name="employee-me"),
    path("auth/logout/", LogoutAPIView.as_view(), name="employee-logout"),
    path("employee/<int:employee_id>/permissions/", EmployeePermissionAPIView.as_view()),

]