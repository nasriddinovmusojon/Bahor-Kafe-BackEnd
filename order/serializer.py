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
            "status",
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


class OrderItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_data = OrderItemWriteSerializer(many=True, write_only=True)  # 🔥 qo‘shildi

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
            "items_data",  # 🔥 qo‘shildi
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

    # 🔥 ENG MUHIM QISM (inventory ulanish)
    def create(self, validated_data, process_sale=None):
        items_data = validated_data.pop("items_data", [])
        user = self.context["request"].user

        order = Order.objects.create(**validated_data)

        total = 0

        for item in items_data:
            product = item["product"]
            quantity = item["quantity"]

            # 🔥 OMBORNI TEKSHIRISH + MINUS
            process_sale(product, quantity, user)

            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity
            )

            # agar productda price bo‘lsa
            if hasattr(product, "price"):
                total += product.price * quantity

        order.total_amount = total
        order.save()

        return order