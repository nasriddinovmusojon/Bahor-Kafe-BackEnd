from datetime import date
import random
from decimal import Decimal
from django.db import models, transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.validators import MinValueValidator


class Order(models.Model):
    """
    Order = butun buyurtmaning o'zi.
    Misol:
        Stol 12
        3 ta mehmon
        Ofitsiant Ali
        Buyurtma holati: ready
        Jami summa: 165000

    Bu modelda buyurtmaning umumiy holati, stol, ofitsiant, summa va vaqtlar saqlanadi.
    """

    class OrderType(models.TextChoices):
        DINE_IN = "dine_in", "Dine in (zalda)"
        TAKEAWAY = "takeaway", "Takeaway (olib ketish)"
        DELIVERY = "delivery", "Delivery (yetkazib berish)"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT_TO_KITCHEN = "sent_to_kitchen", "Oshxonaga yuborildi"
        COOKING = "cooking", "Tayyorlanmoqda"
        READY = "ready", "Tayyor"
        SERVED = "served", "Berildi"
        PAYMENT_PENDING = "payment_pending", "To‘lov kutilmoqda"
        PAID = "paid", "To‘lov olindi"
        CLOSED = "closed", "Yopildi"
        CANCELLED = "cancelled", "Bekor qilindi"


    table = models.ForeignKey(
        "table.Table",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Stol (faqat dine-in bo'lsa to'ladi).",
    )

    type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.DINE_IN,
        help_text="Buyurtma turi.",
    )

    number = models.CharField(
        max_length=20,
        help_text="Buyurtma raqami. Bir kun ichida takrorlanmaydi.",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Buyurtmaning joriy holati.",
    )

    guests_count = models.PositiveIntegerField(
        default=1,
        help_text="Mehmonlar soni.",
    )

    assigned_waiter = models.ForeignKey(
        "employee.Employee",
        on_delete=models.PROTECT,
        related_name="assigned_orders",
        null=True,
        blank=True,
        help_text="Mas'ul ofitsiant.",
    )

    note = models.TextField(
        blank=True,
        default="",
        help_text="Buyurtmaga umumiy izoh.",
    )

    service_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Servis haqi.",
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Yakuniy to'lanadigan summa.",
    )

    sent_to_kitchen_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Buyurtma oshxonaga yuborilgan vaqt.",
    )

    ready_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Buyurtma tayyor bo'lgan vaqt.",
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Buyurtma yopilgan vaqt.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Buyurtma yaratilgan vaqt.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Buyurtma oxirgi marta yangilangan vaqt.",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=[ "number"],
                name="unique_order_number"
            )
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.number} ({self.get_status_display()})"

    def generate_daily_number(self) -> str:
        """
        Maqsad:
            Buyurtma raqamini avtomatik yaratish.

        Qanday ishlaydi:
            - Faqat number bo'sh bo'lsa ishlaydi.
            - Bugungi kunda yaratilgan orderlar orasidan mavjud numberlarni oladi.
            - 001 dan 999 gacha random 3 xonali raqam tanlaydi.
            - Shu kun ichida takrorlanmaydigan raqam topguncha urinadi.

        Eslatma:
            Bu usul kichik/o'rta yuklama uchun ishlaydi.
            Juda katta trafik bo'lsa sequence yoki alohida counter ishlatish yaxshiroq.
        """
        today = date.today()
        existing_numbers = set(
            Order.objects.filter(
                created_at__date=today
            ).values_list("number", flat=True)
        )

        for _ in range(1000):
            rand_number = f"{random.randint(1, 999):03}"
            if rand_number not in existing_numbers:
                return rand_number

        raise ValueError("Bugun uchun bo'sh order raqami qolmadi.")

    def calculate_total(self) -> Decimal:
        """
        Maqsad:
            Buyurtmaning umumiy summasini hisoblash.

        Formula:
            total_amount = barcha order item line_total yig'indisi + service_amount

        Nega alohida metod:
            - qayta ishlatish oson bo'ladi
            - save ichida ham, item o'zgarganda ham chaqirish mumkin
        """
        service_amount = Decimal("1000") * self.guests_count

        items_total = self.items.aggregate(
            total=Coalesce(Sum("line_total"), Decimal("0.00"))
        )["total"]

        return items_total + service_amount

    def recalculate_total(self, save=True):
        """
        Maqsad:
            OrderItem qo'shilganda/o'zgarganda/o'chirilganda
            buyurtmaning total_amount maydonini qayta hisoblash.

        Nega kerak:
            - Kassada to'g'ri summa chiqishi uchun
            - Dashboard va hisobotlarda aniq summa bo'lishi uchun
        """
        self.total_amount = self.calculate_total()

        service_amount = Decimal("1000") * self.guests_count

        if save and self.pk:
            Order.objects.filter(pk=self.pk).update(
                total_amount=self.total_amount,
                service_amount=service_amount,
                updated_at=timezone.now(),
            )

    def save(self, *args, **kwargs):
        """
        Bu modeldagi yagona save metodi.

        Bu save ichida 4 ta asosiy ish bajariladi:

        1) number yaratish
           - Agar buyurtma raqami bo'sh bo'lsa, avtomatik 3 xonali number beriladi.

        2) eski statusni tekshirish
           - Agar bu yangi object bo'lmasa, oldingi status olinadi.
           - Bu vaqt fieldlarini to'g'ri belgilash uchun kerak.

        3) statusga qarab vaqt fieldlarini qo'yish
           - sent_to_kitchen_at: status sent_to_kitchen bo'lganda
           - ready_at: status ready bo'lganda
           - closed_at: status closed bo'lganda

        4) objectni saqlash
           - super().save() orqali DB ga yoziladi

        Muhim:
           total_amount bu yerda hisoblanmaydi, chunki order yangi yaralganda itemlar hali bo'lmasligi mumkin.
           total keyinchalik OrderItem save/delete qilinganda recalculate_total() orqali yangilanadi.
        """
        old_status = None

        if self.pk:
            old_status = Order.objects.filter(pk=self.pk).values_list("status", flat=True).first()

        if not self.number:
            self.number = self.generate_daily_number()

        current_time = timezone.now()

        # Buyurtma oshxonaga yuborilgan vaqt
        if self.status == self.Status.SENT_TO_KITCHEN and not self.sent_to_kitchen_at:
            self.sent_to_kitchen_at = current_time

        # Buyurtma tayyor bo'lgan vaqt
        if self.status == self.Status.READY and not self.ready_at:
            self.ready_at = current_time

        # Buyurtma yopilgan vaqt
        if self.status == self.Status.CLOSED and not self.closed_at:
            self.closed_at = current_time

        # Agar status orqaga qaytsa, vaqtlarni avtomatik tozalash kerak bo'lsa,
        # shu yerda qo'shimcha logika yozish mumkin.
        # Hozircha bir marta qo'yilgan vaqt saqlanib qoladi.

        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    OrderItem = buyurtma ichidagi har bir alohida mahsulot/taom.

    Misol:
        Order: Stol 12
        Itemlar:
            - Margherita x1
            - Cola x2
            - Burger x1

    Shu qatorlarning har biri alohida OrderItem bo'ladi.
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Qaysi buyurtmaga tegishli.",
    )

    product = models.ForeignKey(
        "table.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        help_text="Mahsulot o'chsa NULL bo'ladi.",
    )

    # Snapshot fieldlar:
    # Mahsulot nomi keyinchalik o'zgarsa ham eski orderda asl nom saqlanib qoladi.
    product_name_snapshot = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Mahsulot nomining buyurtma paytidagi nusxasi.",
    )

    kitchen_name_snapshot = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Oshxona uchun ko'rinadigan nomning nusxasi.",
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Bir dona narxi.",
    )

    qty = models.PositiveIntegerField(
        default=1,
        help_text="Mahsulot soni.",
    )

    line_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
        help_text="Umumiy summa = unit_price x qty.",
    )

    note = models.TextField(
        blank=True,
        default="",
        help_text="Aynan shu item uchun izoh. Masalan: achchiq bo'lmasin.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Yaratilgan vaqt.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Oxirgi yangilangan vaqt.",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        item_name = self.product_name_snapshot or (self.product.name if self.product else "Deleted product")
        return f"{item_name} x {self.qty}"

    def save(self, *args, **kwargs):
        """
        Bu save ichida 4 ta asosiy ish bajariladi:

        1) Snapshot fieldlarni to'ldirish
           - product bor bo'lsa, nomi va oshxona nomini saqlab qo'yadi
           - keyinchalik product nomi o'zgarsa ham eski order tarixiy jihatdan buzilmaydi

        2) line_total ni avtomatik hisoblash
           - unit_price * qty
           - frontend line_total yuborishiga ishonilmaydi

        3) OrderItem ni saqlash

        4) Shu item tegishli bo'lgan orderning umumiy summasini qayta hisoblash
           - order.total_amount yangilanadi
        """
        if self.product:
            if not self.product_name_snapshot:
                self.product_name_snapshot = getattr(self.product, "name", "") or ""
            if not self.kitchen_name_snapshot:
                self.kitchen_name_snapshot = getattr(self.product, "kitchen_name", "") or getattr(self.product, "name", "") or ""

        self.line_total = self.unit_price * self.qty

        super().save(*args, **kwargs)

        # Item saqlangandan keyin order total qayta hisoblanadi
        if self.order_id:
            self.order.recalculate_total()

    def delete(self, *args, **kwargs):
        """
        Maqsad:
            Item o'chirilganda ham order total_amount noto'g'ri bo'lib qolmasligi kerak.

        Qanday ishlaydi:
            - Avval order reference ni olib qolamiz
            - Itemni o'chiramiz
            - Keyin order totalni qayta hisoblaymiz
        """
        order = self.order
        super().delete(*args, **kwargs)

        if order:
            order.recalculate_total()


class Payment(models.Model):
    class PaymentType(models.TextChoices):
        CASH = "cash", "Naqd"
        CARD = "card", "Karta"
        MIXED = "mixed", "Aralash"

    order = models.OneToOneField(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="payment",
        help_text="Qaysi buyurtma uchun to‘lov qilingan."
    )

    payment_type = models.CharField(
        max_length=10,
        choices=PaymentType.choices,
        help_text="To‘lov turi."
    )

    cash_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
        help_text="Naqd to‘langan summa."
    )

    card_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
        help_text="Karta orqali to‘langan summa."
    )

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Jami to‘langan summa."
    )

    note = models.TextField(
        blank=True,
        default="",
        help_text="Qo‘shimcha izoh."
    )


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment_type"]),
        ]

    def __str__(self):
        return f"Payment #{self.id} - Order {self.order.number}"

    def clean_amounts(self):
        total = self.order.total_amount or Decimal("0.00")
        cash = self.cash_amount or Decimal("0.00")
        card = self.card_amount or Decimal("0.00")

        if self.payment_type == self.PaymentType.CASH:
            self.card_amount = Decimal("0.00")
            self.paid_amount = cash
            self.change_amount = max(cash - total, Decimal("0.00"))

        elif self.payment_type == self.PaymentType.CARD:
            self.cash_amount = Decimal("0.00")
            self.change_amount = Decimal("0.00")
            self.paid_amount = card

        elif self.payment_type == self.PaymentType.MIXED:
            self.paid_amount = cash + card
            self.change_amount = max((cash + card) - total, Decimal("0.00"))

    def validate_payment(self):
        total = self.order.total_amount or Decimal("0.00")

        if self.payment_type == self.PaymentType.CASH and self.cash_amount < total:
            raise ValueError("Naqd summa jami summadan kam bo‘lishi mumkin emas.")

        if self.payment_type == self.PaymentType.CARD and self.card_amount < total:
            raise ValueError("Karta summasi jami summadan kam bo‘lishi mumkin emas.")

        if self.payment_type == self.PaymentType.MIXED and (self.cash_amount + self.card_amount) < total:
            raise ValueError("Aralash to‘lovda jami summa yetarli emas.")

    def save(self, *args, **kwargs):
        self.clean_amounts()
        self.validate_payment()

        with transaction.atomic():
            super().save(*args, **kwargs)

            # Order statusni paid qilish
            self.order.status = self.order.Status.PAID
            self.order.save(update_fields=["status", "updated_at"])