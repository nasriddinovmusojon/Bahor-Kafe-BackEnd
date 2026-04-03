from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import KitchenTicket
from .serializer import KitchenTicketSerializer, KitchenTicketStatusSerializer


class KitchenTicketViewSet(viewsets.ModelViewSet):
    """
    KitchenTicket uchun production-ga yaqin ViewSet.

    Imkoniyatlar:
    - list / retrieve / create / update / delete
    - status bo‘yicha filter
    - order bo‘yicha filter
    - faqat status update uchun maxsus endpoint
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Query optimizatsiya:
        - order
        - sent_by
        oldindan select_related bilan olinadi

        Filterlar:
        - ?status=
        - ?order=
        """
        queryset = (
            KitchenTicket.objects
            .select_related("order", "sent_by")
            .all()
            .order_by("-created_at")
        )

        status_param = self.request.query_params.get("status")
        order_param = self.request.query_params.get("order")

        if status_param:
            queryset = queryset.filter(status=status_param)

        if order_param:
            queryset = queryset.filter(order_id=order_param)

        return queryset

    def get_serializer_class(self):
        """
        Agar custom status action bo‘lsa,
        status serializer ishlatiladi.
        """
        if self.action == "update_status":
            return KitchenTicketStatusSerializer
        return KitchenTicketSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        """
        Yangi kitchen ticket yaratish.

        Agar request.user bilan employee bog‘langan bo‘lsa,
        sent_by ni avtomatik qo‘yishga urinadi.
        """
        employee = getattr(self.request.user, "employee", None)

        if employee and "sent_by" not in serializer.validated_data:
            serializer.save(sent_by=employee)
        else:
            serializer.save()

    @transaction.atomic
    def perform_update(self, serializer):
        """
        Oddiy update uchun transaction.
        """
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        """
        Delete uchun transaction.

        Productionda ko‘pincha delete o‘rniga cancel ishlatiladi.
        Hozircha delete qoldirilgan.
        """
        instance.delete()

    @action(detail=True, methods=["patch"])
    @transaction.atomic
    def update_status(self, request, pk=None):
        """
        Faqat statusni yangilash endpointi.

        Endpoint:
            PATCH /api/kitchen-tickets/{id}/update_status/

        Body:
            {
                "status": "COOKING"
            }
        """
        ticket = self.get_object()

        serializer = self.get_serializer(
            ticket,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            KitchenTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def mark_cooking(self, request, pk=None):
        """
        Tezkor action:
            POST /api/kitchen-tickets/{id}/mark_cooking/
        """
        ticket = self.get_object()

        serializer = KitchenTicketStatusSerializer(
            ticket,
            data={"status": KitchenTicket.Status.COOKING},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            KitchenTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def mark_ready(self, request, pk=None):
        """
        Tezkor action:
            POST /api/kitchen-tickets/{id}/mark_ready/
        """
        ticket = self.get_object()

        serializer = KitchenTicketStatusSerializer(
            ticket,
            data={"status": KitchenTicket.Status.READY},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            KitchenTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        """
        Tezkor action:
            POST /api/kitchen-tickets/{id}/cancel/
        """
        ticket = self.get_object()

        serializer = KitchenTicketStatusSerializer(
            ticket,
            data={"status": KitchenTicket.Status.CANCELLED},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            KitchenTicketSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK
        )