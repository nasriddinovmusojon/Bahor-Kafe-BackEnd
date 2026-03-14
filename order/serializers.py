from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "product",
            "product_name_snapshot",
            "kitchen_name_snapshot",
            "unit_price",
            "qty",
            "line_total",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "line_total",
            "product_name_snapshot",
            "kitchen_name_snapshot",
            "created_at",
            "updated_at",
        ]

    def validate_qty(self, value):
        if value < 1:
            raise serializers.ValidationError("Miqdor kamida 1 bo‘lishi kerak.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo‘lishi mumkin emas.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "table",
            "type",
            "number",
            "status",
            "guests_count",
            "assigned_waiter",
            "note",
            "service_amount",
            "total_amount",
            "sent_to_kitchen_at",
            "ready_at",
            "closed_at",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "number",
            "total_amount",
            "sent_to_kitchen_at",
            "ready_at",
            "closed_at",
            "created_at",
            "updated_at",
        ]

    def validate_guests_count(self, value):
        if value < 1:
            raise serializers.ValidationError("Mehmonlar soni kamida 1 bo‘lishi kerak.")
        return value

    def validate(self, attrs):
        order_type = attrs.get("type", getattr(self.instance, "type", None))
        table = attrs.get("table", getattr(self.instance, "table", None))
        assigned_waiter = attrs.get("assigned_waiter", getattr(self.instance, "assigned_waiter", None))

        if order_type == Order.OrderType.DINE_IN and not table:
            raise serializers.ValidationError({
                "table": "Dine-in buyurtma uchun stol tanlanishi shart."
            })

        if order_type in [Order.OrderType.TAKEAWAY, Order.OrderType.DELIVERY] and table:
            raise serializers.ValidationError({
                "table": "Takeaway yoki delivery buyurtmada stol bo‘lmasligi kerak."
            })

        if assigned_waiter and getattr(assigned_waiter, "role", None) != "WAITER":
            raise serializers.ValidationError({
                "assigned_waiter": "Mas'ul xodimning roli WAITER bo‘lishi kerak."
            })

        return attrs

from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)
    order_total = serializers.DecimalField(source="order.total_amount", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "order_number",
            "order_total",
            "payment_type",
            "cash_amount",
            "card_amount",
            "paid_amount",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "paid_amount",
            "created_at",
            "updated_at",
            "order_number",
            "order_total",
        ]

    def validate(self, attrs):
        order = attrs.get("order")
        payment_type = attrs.get("payment_type")
        cash_amount = attrs.get("cash_amount", 0)
        card_amount = attrs.get("card_amount", 0)

        if hasattr(order, "payment"):
            raise serializers.ValidationError({"order": "Bu order uchun to‘lov allaqachon qilingan."})

        if order.status in [order.Status.CLOSED, order.Status.CANCELLED]:
            raise serializers.ValidationError({"order": "Yopilgan yoki bekor qilingan order uchun to‘lov qilib bo‘lmaydi."})

        if payment_type == Payment.PaymentType.CASH and cash_amount <= 0:
            raise serializers.ValidationError({"cash_amount": "Naqd summa kiritilishi shart."})

        if payment_type == Payment.PaymentType.CARD and card_amount <= 0:
            raise serializers.ValidationError({"card_amount": "Karta summa kiritilishi shart."})

        if payment_type == Payment.PaymentType.MIXED and (cash_amount + card_amount) <= 0:
            raise serializers.ValidationError("Aralash to‘lov uchun summa kiritilishi shart.")

        return attrs