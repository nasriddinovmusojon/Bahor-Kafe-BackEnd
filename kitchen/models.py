from django.db import models


class KitchenTicket(models.Model):
    """
    KitchenTicket = oshxonaga yuborilgan buyurtma.

    Order oshxonaga yuborilganda yaratiladi.
    Kitchen Display System shu ticket orqali ishlaydi.
    """

    class Status(models.TextChoices):
        NEW = "NEW", "Yangi"
        COOKING = "COOKING", "Tayyorlanmoqda"
        READY = "READY", "Tayyor"
        CANCELLED = "CANCELLED", "Bekor qilindi"

    order = models.OneToOneField(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="kitchen_ticket",
        help_text="Bog‘langan buyurtma."
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Oshxona jarayon holati."
    )

    sent_by = models.ForeignKey(
        "employee.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_kitchen_tickets",
        help_text="Ticketni yuborgan xodim."
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Oshxona tayyorlashni boshlagan vaqt."
    )

    ready_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Taom tayyor bo‘lgan vaqt."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Ticket yaratilgan vaqt."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Oxirgi yangilanish."
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Ticket #{self.id} | Order {self.order.number} | {self.status}"