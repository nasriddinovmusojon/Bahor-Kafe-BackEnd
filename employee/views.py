from django.contrib.auth import get_user_model
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveUpdateAPIView
from .serializer import EmployeePermissionSerializer
from .models import EmployeePermission

from .models import Employee
from .serializer import (
    EmployeeSerializer,
    EmployeeCreateSerializer,
    LoginSerializer,
    PinSetSerializer,
    PinLoginSerializer,
    MeSerializer,
)

User = get_user_model()


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Employee CRUD
    Admin uchun xodim yaratish, ko‘rish, tahrirlash.
    """
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        queryset = (
            Employee.objects
            .select_related("user")
            .all()
            .order_by("name")
        )

        role = self.request.query_params.get("role")
        is_active = self.request.query_params.get("is_active")
        search = self.request.query_params.get("search")

        if role:
            queryset = queryset.filter(role=role)

        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(is_active=False)

        if search:
            queryset = queryset.filter(name__icontains=search.strip())

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        return EmployeeSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save()


class LoginAPIView(APIView):
    """
    Birinchi kirish:
    phone + password
    natijada token qaytadi
    """
    permission_classes = []

    @swagger_auto_schema(request_body=LoginSerializer, responses={200: LoginSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        employee = serializer.validated_data["employee"]

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "employee": MeSerializer(employee).data,
            "message": "Muvaffaqiyatli login qilindi."
        }, status=status.HTTP_200_OK)


class SetPinAPIView(APIView):
    """
    Login bo‘lgan foydalanuvchi 4 xonali PIN o‘rnatadi.
    Header:
        Authorization: Token <token>
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=PinSetSerializer, responses={200: PinSetSerializer})
    def post(self, request):
        serializer = PinSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            return Response(
                {"detail": "Xodim profili topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        employee.quick_pin = serializer.validated_data["quick_pin"]
        employee.pin_is_set = True
        employee.save(update_fields=["quick_pin", "pin_is_set", "updated_at"])

        return Response({
            "message": "PIN muvaffaqiyatli o‘rnatildi."
        }, status=status.HTTP_200_OK)


class PinLoginAPIView(APIView):
    """
    Keyingi kirish:
    phone + 4 xonali pin
    natijada token qaytadi
    """
    permission_classes = []
    @swagger_auto_schema(request_body=PinLoginSerializer, responses={200: PinLoginSerializer})
    def post(self, request):
        serializer = PinLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        employee = serializer.validated_data["employee"]

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "employee": MeSerializer(employee).data,
            "message": "PIN orqali muvaffaqiyatli login qilindi."
        }, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    """
    Token orqali hozirgi login bo‘lgan xodimni qaytaradi.
    """
    permission_classes = [IsAuthenticated]
    # @swagger_auto_schema(request_body=MeSerializer, responses={200: MeSerializer})
    def get(self, request):
        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            return Response(
                {"detail": "Xodim profili topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(MeSerializer(employee).data, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    """
    Tokenni o‘chiradi.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response({"message": "Logout qilindi."}, status=status.HTTP_200_OK)



class EmployeePermissionAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeePermissionSerializer

    def get_object(self):
        employee_id = self.kwargs.get("employee_id")
        return EmployeePermission.objects.get(employee_id=employee_id)