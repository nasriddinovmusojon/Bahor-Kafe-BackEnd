from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        "product",
        "product_name_snapshot",
        "unit_price",
        "qty",
        "line_total",
        "note",
    )
    readonly_fields = ("line_total", "product_name_snapshot")
    autocomplete_fields = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "number",
        "type",
        "status",
        "table",
        "assigned_waiter",
        "guests_count",
        "total_amount",
        "created_at",
    )
    list_filter = (
        "type",
        "status",
        "created_at",
        "assigned_waiter",
    )
    search_fields = (
        "number",
        "note",
        "table__name",
        "assigned_waiter__name",
    )
    readonly_fields = (
        "number",
        "total_amount",
        "sent_to_kitchen_at",
        "ready_at",
        "closed_at",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("table", "assigned_waiter")
    inlines = [OrderItemInline]
    ordering = ("-created_at",)
    list_per_page = 20

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": (
                "number",
                "type",
                "status",
                "table",
                "assigned_waiter",
                "guests_count",
                "note",
            )
        }),
        ("Summalar", {
            "fields": (
                "service_amount",
                "total_amount",
            )
        }),
        ("Vaqtlar", {
            "fields": (
                "sent_to_kitchen_at",
                "ready_at",
                "closed_at",
                "created_at",
                "updated_at",
            )
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_name_snapshot",
        "unit_price",
        "qty",
        "line_total",
        "created_at",
    )
    list_filter = (
        "created_at",
    )
    search_fields = (
        "order__number",
        "product_name_snapshot",
        "kitchen_name_snapshot",
        "note",
    )
    readonly_fields = (
        "line_total",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("order", "product")
    ordering = ("-created_at",)
    list_per_page = 30