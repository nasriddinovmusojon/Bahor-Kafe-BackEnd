from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import Employee

User = get_user_model()


class EmployeeSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "phone",
            "role",
            "quick_pin",
            "pin_is_set",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "pin_is_set",
            "created_at",
            "updated_at",
            "phone",
        ]
        extra_kwargs = {
            "quick_pin": {"write_only": True},
        }

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Xodim ismi bo‘sh bo‘lishi mumkin emas.")
        return value


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """
    Admin yangi xodim yaratganda ishlatiladi.
    Shu yerda User ham, Employee ham birga yaratiladi.
    """
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "phone",
            "password",
            "role",
            "is_active",
        ]

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon mavjud.")
        return value

    def create(self, validated_data):
        phone = validated_data.pop("phone")
        password = validated_data.pop("password")

        user = User.objects.create(phone=phone)
        user.set_password(password)
        user.save()

        employee = Employee.objects.create(user=user, **validated_data)
        return employee


class LoginSerializer(serializers.Serializer):
    """
    Birinchi login:
    phone + password
    natijada token qaytadi
    """
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Telefon yoki parol noto‘g‘ri."})

        if not user.check_password(password):
            raise serializers.ValidationError({"detail": "Telefon yoki parol noto‘g‘ri."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Foydalanuvchi faol emas."})

        try:
            employee = user.employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError({"detail": "Xodim profili topilmadi."})

        if not employee.is_active:
            raise serializers.ValidationError({"detail": "Xodim faol emas."})

        attrs["user"] = user
        attrs["employee"] = employee
        return attrs


class PinSetSerializer(serializers.Serializer):
    """
    Login qilgan xodim 4 xonali pin o‘rnatadi.
    """
    quick_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)
    confirm_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)

    def validate_quick_pin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("PIN faqat raqamlardan iborat bo‘lishi kerak.")
        return value

    def validate(self, attrs):
        quick_pin = attrs.get("quick_pin")
        confirm_pin = attrs.get("confirm_pin")

        if quick_pin != confirm_pin:
            raise serializers.ValidationError({"confirm_pin": "PIN lar mos emas."})

        return attrs


class PinLoginSerializer(serializers.Serializer):
    """
    Keyingi login:
    phone + 4 xonali pin
    """
    phone = serializers.CharField()
    quick_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)

    def validate(self, attrs):
        phone = attrs.get("phone")
        quick_pin = attrs.get("quick_pin")

        if not quick_pin.isdigit():
            raise serializers.ValidationError({"quick_pin": "PIN faqat 4 ta raqam bo‘lishi kerak."})

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Telefon yoki PIN noto‘g‘ri."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Foydalanuvchi faol emas."})

        try:
            employee = user.employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError({"detail": "Xodim profili topilmadi."})

        if not employee.is_active:
            raise serializers.ValidationError({"detail": "Xodim faol emas."})

        if not employee.pin_is_set:
            raise serializers.ValidationError({"detail": "Bu xodim hali PIN o‘rnatmagan."})

        if employee.quick_pin != quick_pin:
            raise serializers.ValidationError({"detail": "Telefon yoki PIN noto‘g‘ri."})

        attrs["user"] = user
        attrs["employee"] = employee
        return attrs


class MeSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "phone",
            "role",
            "pin_is_set",
            "is_active",
        ]




from .models import EmployeePermission

class EmployeePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePermission
        fields = [
            "can_payment",
            "can_discount",
            "can_cancel_order",
            "can_income",
            "permissions"
        ]