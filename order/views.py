from django.db import transaction
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Order, OrderItem
from .serializer import OrderSerializer, OrderItemSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    OrderViewSet
    ----------------
    Bu ViewSet buyurtmalar bilan ishlaydi.

    Oddiy CRUD dan tashqari quyidagi custom actionlar bor:
    - send_to_kitchen
    - mark_ready
    - mark_served
    - mark_paid
    - cancel
    - add_item
    - remove_item

    Query params orqali filterlar:
    - ?status=
    - ?table=
    - ?type=
    - ?assigned_waiter=
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Querysetni optimizatsiya qilamiz:
        - table
        - assigned_waiter
        - items
        oldindan olib kelinadi.

        Query params bo'yicha filter qilamiz.
        """
        queryset = (
            Order.objects
            .select_related("table", "assigned_waiter")
            .prefetch_related("items")
            .all()
            .order_by("-created_at")
        )

        status_param = self.request.query_params.get("status")
        table_param = self.request.query_params.get("table")
        type_param = self.request.query_params.get("type")
        waiter_param = self.request.query_params.get("assigned_waiter")

        if status_param:
            queryset = queryset.filter(status=status_param)

        if table_param:
            queryset = queryset.filter(table_id=table_param)

        if type_param:
            queryset = queryset.filter(type=type_param)

        if waiter_param:
            queryset = queryset.filter(assigned_waiter_id=waiter_param)

        return queryset

    def perform_create(self, serializer):
        """
        Yangi order yaratilganda qo'shimcha logika.

        Hozir:
        - agar frontend assigned_waiter yubormagan bo'lsa,
          request.user ga bog'liq employee ni avtomatik qo'yishga urinadi.

        Agar sizda request.user -> employee bog'lanishi boshqa nomda bo'lsa,
        shu joyni moslab o'zgartirasiz.
        """
        assigned_waiter = serializer.validated_data.get("assigned_waiter")

        if not assigned_waiter:
            employee = getattr(self.request.user, "employee", None)
            if employee:
                serializer.save(assigned_waiter=employee)
                return

        serializer.save()

    # POST /api/orders/5/send_to_kitchen/
    @action(detail=True, methods=["post"])
    def send_to_kitchen(self, request, pk=None):
        """
        Buyurtmani oshxonaga yuborish.

        Qoidalar:
        - faqat draft yoki cooking bo'lmagan holatda ishlashi kerak
        - order status = sent_to_kitchen bo'ladi
        - sent_to_kitchen_at model save ichida avtomatik qo'yiladi
        """
        order = self.get_object()

        if order.status == Order.Status.CANCELLED:
            return Response(
                {"detail": "Bekor qilingan buyurtmani oshxonaga yuborib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status == Order.Status.CLOSED:
            return Response(
                {"detail": "Yopilgan buyurtmani oshxonaga yuborib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not order.items.exists():
            return Response(
                {"detail": "Bo‘sh buyurtmani oshxonaga yuborib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status == Order.Status.SENT_TO_KITCHEN:
            return Response(
                {"detail": "Buyurtma allaqachon oshxonaga yuborilgan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.SENT_TO_KITCHEN
        order.save()

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def mark_ready(self, request, pk=None):
        """
        Buyurtmani tayyor deb belgilash.

        Odatda bu action oshxona tomondan ishlatiladi.
        """
        order = self.get_object()

        if order.status in [Order.Status.CANCELLED, Order.Status.CLOSED]:
            return Response(
                {"detail": "Bekor qilingan yoki yopilgan buyurtmani READY qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status not in [Order.Status.SENT_TO_KITCHEN, Order.Status.COOKING]:
            return Response(
                {"detail": "Faqat oshxonaga yuborilgan yoki tayyorlanayotgan buyurtma READY bo‘lishi mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.READY
        order.save()

        # Istasangiz shu yerda itemlarni ham READY qilishingiz mumkin
        order.items.exclude(status=OrderItem.Status.CANCELLED).update(status=OrderItem.Status.READY)

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def mark_served(self, request, pk=None):
        """
        Buyurtma mijozga berilganini belgilash.
        """
        order = self.get_object()

        if order.status != Order.Status.READY:
            return Response(
                {"detail": "Faqat READY holatidagi buyurtma SERVED bo‘lishi mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.SERVED
        order.save()

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        """
        Buyurtma to'langanini belgilash.

        Hozircha soddalashtirilgan.
        Keyin payment model qo'shsangiz shu joyda transaction bilan yoziladi.
        """
        order = self.get_object()

        if order.status in [Order.Status.CANCELLED, Order.Status.CLOSED]:
            return Response(
                {"detail": "Bekor qilingan yoki yopilgan buyurtmani PAID qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.total_amount <= 0:
            return Response(
                {"detail": "Jami summa 0 bo‘lgan buyurtmani to‘langan deb belgilab bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.PAID
        order.save()

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def close_order(self, request, pk=None):
        """
        Buyurtmani yopish.

        Odatda:
        - PAID bo'lgan order yopiladi
        """
        order = self.get_object()

        if order.status != Order.Status.PAID:
            return Response(
                {"detail": "Faqat to‘langan buyurtmani yopish mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.CLOSED
        order.save()

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Buyurtmani bekor qilish.

        Istasangiz keyin reason ham majburiy qilishingiz mumkin.
        """
        order = self.get_object()

        if order.status in [Order.Status.PAID, Order.Status.CLOSED]:
            return Response(
                {"detail": "To‘langan yoki yopilgan buyurtmani bekor qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.Status.CANCELLED
        order.save()

        order.items.update(status=OrderItem.Status.CANCELLED)

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    # POST /api/orders/5/add_item/
    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        """
        Berilgan orderga yangi item qo'shish.

        Request body misol:
        {
            "product": 1,
            "unit_price": "25000.00",
            "qty": 2,
            "note": "achchiq bo‘lmasin"
        }
        """
        order = self.get_object()

        if order.status in [Order.Status.CANCELLED, Order.Status.CLOSED]:
            return Response(
                {"detail": "Bekor qilingan yoki yopilgan buyurtmaga item qo‘shib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data["order"] = order.id

        serializer = OrderItemSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        order.refresh_from_db()

        return Response(
            {
                "detail": "Item muvaffaqiyatli qo‘shildi.",
                "order": OrderSerializer(order, context={"request": request}).data,
                "item": serializer.data,
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="remove-item/(?P<item_id>[^/.]+)")
    def remove_item(self, request, pk=None, item_id=None):
        """
        Order ichidagi itemni o'chirish.

        URL misol:
        POST /api/orders/5/remove-item/12/
        """
        order = self.get_object()

        if order.status in [Order.Status.CANCELLED, Order.Status.CLOSED]:
            return Response(
                {"detail": "Bekor qilingan yoki yopilgan buyurtmadan item o‘chirib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = order.items.get(pk=item_id)
        except OrderItem.DoesNotExist:
            return Response(
                {"detail": "Item topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()
        order.refresh_from_db()

        return Response(
            {
                "detail": "Item muvaffaqiyatli o‘chirildi.",
                "order": OrderSerializer(order, context={"request": request}).data,
            },
            status=status.HTTP_200_OK
        )


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    OrderItemViewSet
    ----------------
    Order itemlar bilan ishlash uchun.

    Odatda productionda itemlar ko'proq Order ichida boshqariladi.
    Lekin alohida endpoint ham foydali bo'lishi mumkin.

    Query params:
    - ?order=
    - ?status=
    """

    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            OrderItem.objects
            .select_related("order", "product")
            .all()
            .order_by("-created_at")
        )

        order_param = self.request.query_params.get("order")
        status_param = self.request.query_params.get("status")

        if order_param:
            queryset = queryset.filter(order_id=order_param)

        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        """
        Item yaratishda transaction ishlatamiz.

        Nega:
        - item save bo'ladi
        - line_total hisoblanadi
        - order total qayta hisoblanadi

        Hammasi bitta transaction ichida bo'lsa xavfsizroq.
        """
        serializer.save()

    @transaction.atomic
    def perform_update(self, serializer):
        """
        Item update bo'lganda ham transaction.
        """
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        """
        Item o'chirilganda ham transaction.
        """
        instance.delete()

    @action(detail=True, methods=["post"])
    def mark_cooking(self, request, pk=None):
        """
        Item holatini COOKING qilish.
        """
        item = self.get_object()

        if item.status == OrderItem.Status.CANCELLED:
            return Response(
                {"detail": "Bekor qilingan itemni cooking qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.status = OrderItem.Status.COOKING
        item.save()

        return Response(
            OrderItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def mark_ready(self, request, pk=None):
        """
        Item holatini READY qilish.
        """
        item = self.get_object()

        if item.status == OrderItem.Status.CANCELLED:
            return Response(
                {"detail": "Bekor qilingan itemni ready qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.status = OrderItem.Status.READY
        item.save()

        return Response(
            OrderItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Itemni bekor qilish.
        """
        item = self.get_object()

        if item.order.status in [Order.Status.PAID, Order.Status.CLOSED]:
            return Response(
                {"detail": "To‘langan yoki yopilgan buyurtmadagi itemni bekor qilib bo‘lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.status = OrderItem.Status.CANCELLED
        item.save()

        return Response(
            OrderItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_200_OK
        )