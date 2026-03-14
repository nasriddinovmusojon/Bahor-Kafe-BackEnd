from django.contrib import admin
from .models import Employee, User
from django.contrib.auth.admin import UserAdmin


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ("phone", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "password1", "password2", "is_staff", "is_superuser", "is_active"),
        }),
    )

    search_fields = ("phone",)
    ordering = ("phone",)
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    Employee admin paneli.
    Maqsad:
    - xodimlarni qulay ko‘rish
    - role bo‘yicha filtrlash
    - phone va ism bo‘yicha qidirish
    - pin va vaqt fieldlarni tartibli ko‘rsatish
    """

    list_display = (
        "id",
        "name",
        "get_phone",
        "role",
        "pin_is_set",
        "is_active",
        "created_at",
    )

    list_display_links = ("id", "name")

    list_filter = (
        "role",
        "pin_is_set",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "user__phone",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": (
                "user",
                "name",
                "role",
                "is_active",
            )
        }),
        ("PIN sozlamalari", {
            "fields": (
                "quick_pin",
                "pin_is_set",
            )
        }),
        ("Vaqt ma'lumotlari", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    ordering = ("name",)

    def get_phone(self, obj):
        return obj.user.phone if obj.user else "-"
    get_phone.short_description = "Telefon"