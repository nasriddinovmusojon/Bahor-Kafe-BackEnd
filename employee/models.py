# employee/models.py
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqami kiritilishi shart")

        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser uchun is_staff=True bo‘lishi kerak")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser uchun is_superuser=True bo‘lishi kerak")

        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    username = None

    phone_validator = RegexValidator(
        regex=r'^\+998\d{9}$',
        message="Telefon raqami +998 bilan boshlanishi kerak."
    )

    phone = models.CharField(
        max_length=13,
        unique=True,
        validators=[phone_validator]
    )

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone

class Employee(models.Model):
    class Role(models.TextChoices):
        WAITER = "WAITER", "Ofitsiant"
        KITCHEN = "KITCHEN", "Oshpaz"
        CASHIER = "CASHIER", "Kassir"
        MANAGER = "MANAGER", "Menejer"
        ADMIN = "ADMIN", "Administrator"

    pin_validator = RegexValidator(
        regex=r'^\d{4}$',
        message="PIN kod 4 xonali bo‘lishi kerak."
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee"
    )

    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices)
    quick_pin = models.CharField(max_length=4, blank=True, default="", validators=[pin_validator])
    pin_is_set = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class EmployeePermission(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="permissions"
    )

    # POS
    can_payment = models.BooleanField(default=False)
    can_discount = models.BooleanField(default=False)

    # Buyurtmalar
    can_cancel_order = models.BooleanField(default=False)

    # Ombor
    can_income = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee.name} permissions"