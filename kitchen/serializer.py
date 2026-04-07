from django.utils import timezone
from rest_framework import serializers

from .models import KitchenTicket
from order.models import Order


class KitchenTicketSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)
    order_status = serializers.CharField(source="order.status", read_only=True)
    sent_by_name = serializers.CharField(source="sent_by.name", read_only=True)

    class Meta:
        model = KitchenTicket
        fields = [
            "id",
            "order",
            "order_number",
            "order_status",
            "status",
            "sent_by",
            "sent_by_name",
            "started_at",
            "ready_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "started_at",
            "ready_at",
            "created_at",
            "updated_at",
            "order_number",
            "order_status",
            "sent_by_name",
        ]

    def validate(self, attrs):
        """
        KitchenTicket yaratishda asosiy tekshiruvlar:
        - bir order uchun bitta ticket bo‘lishi kerak
        """
        order = attrs.get("order")

        if self.instance is None and order:
            if KitchenTicket.objects.filter(order=order).exists():
                raise serializers.ValidationError({
                    "order": "Bu buyurtma uchun kitchen ticket allaqachon mavjud."
                })

        return attrs


class KitchenTicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = KitchenTicket
        fields = ["status"]

    def validate_status(self, value):
        """
        Status uchun basic validatsiya.
        """
        allowed_statuses = {
            KitchenTicket.Status.NEW,
            KitchenTicket.Status.COOKING,
            KitchenTicket.Status.READY,
            KitchenTicket.Status.CANCELLED,
        }
        if value not in allowed_statuses:
            raise serializers.ValidationError("Noto‘g‘ri status.")
        return value

    def update(self, instance, validated_data):
        """
        Bu serializer faqat statusni update qiladi.

        Qo‘shimcha logika:
        - COOKING bo‘lsa started_at yoziladi
        - READY bo‘lsa ready_at yoziladi
        - Order status ham mos ravishda update qilinadi
        """
        new_status = validated_data.get("status")
        current_time = timezone.now()

        instance.status = new_status

        if new_status == KitchenTicket.Status.COOKING and not instance.started_at:
            instance.started_at = current_time

        if new_status == KitchenTicket.Status.READY and not instance.ready_at:
            instance.ready_at = current_time

        instance.save(update_fields=["status", "started_at", "ready_at", "updated_at"])

        # Order statusni ham moslashtiramiz
        order = instance.order

        if new_status == KitchenTicket.Status.COOKING:
            order.status = Order.Status.COOKING
            order.save(update_fields=["status", "updated_at"])

        elif new_status == KitchenTicket.Status.READY:
            order.status = Order.Status.READY
            order.ready_at = current_time
            order.save(update_fields=["status", "ready_at", "updated_at"])

        elif new_status == KitchenTicket.Status.CANCELLED:
            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status", "updated_at"])

        elif new_status == KitchenTicket.Status.NEW:
            # Odatda orqaga qaytish kam ishlatiladi, lekin qo‘lda ruxsat berilsa
            order.status = Order.Status.SENT_TO_KITCHEN
            order.save(update_fields=["status", "updated_at"])

        return instance