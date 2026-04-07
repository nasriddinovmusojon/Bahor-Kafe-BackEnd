from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

# =========================
# TABLE
# =========================
class Table(models.Model):
    """
    Table = restorandagi stol modeli.

    Vazifasi:
    - Ofitsiant buyurtma qabul qilayotganda qaysi stolga buyurtma ochilganini bilish
    - Kassir stol bo‘yicha buyurtmani topishi
    - Stolning joriy holatini ko‘rsatish

    Hozircha branch ulanmagan.
    Keyingi bosqichda filial qo‘shilsa, shu modelga branch FK qo‘shiladi.
    """

    class Status(models.TextChoices):
        FREE = "free", "Bo‘sh"
        BUSY = "busy", "Band"
        PAYMENT = "payment", "Hisob jarayonida"

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stol nomi yoki raqami. Masalan: 1-stol, VIP-1."
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.FREE,
        help_text="Stolning joriy holati."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Stol faol yoki nofaol ekanini bildiradi."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Stol yaratilgan vaqt."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Stol oxirgi marta yangilangan vaqt."
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


# =========================
# CATEGORY
# =========================
class Category(models.Model):
    """
    Category = mahsulot kategoriyasi.

    Misol:
    - Pitsa
    - Burger
    - Ichimlik
    - Desert

    Vazifasi:
    - Mahsulotlarni guruhlarga ajratish
    - Ofitsiant ekranida kategoriyalarni chiqarish
    - Menyu boshqaruvida tartibni saqlash
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Kategoriya nomi."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Kategoriya faol yoki nofaol ekanini bildiradi."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Kategoriya yaratilgan vaqt."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Kategoriya oxirgi marta yangilangan vaqt."
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


# =========================
# PRODUCT
# =========================
class Product(models.Model):
    UNIT_CHOICES = (
        ("g", "Gram"),
        ("dona", "Dona"),
        ("litr", "Litr"),
    )
    # """
    # Product = menyudagi mahsulot yoki taom.
    #
    # Misol:
    # - Margherita
    # - Cola
    # - Cheeseburger
    #
    # Vazifasi:
    # - Ofitsiant oynasida tanlanadigan taomlar ro‘yxati
    # - Oshxonaga ketadigan mahsulot nomlari
    # - Kassada hisoblanadigan narx
    # """

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        help_text="Mahsulot qaysi kategoriyaga tegishli."
    )

    name = models.CharField(
        max_length=255,
        help_text="Mahsulotning asosiy nomi."
    )

    kitchen_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Oshxonada ko‘rinadigan nom. Bo‘sh bo‘lsa name bilan bir xil bo‘ladi."
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Mahsulot narxi."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Mahsulot sotuvda faol yoki yo‘qligi."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Mahsulot yaratilgan vaqt."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Mahsulot oxirgi marta yangilangan vaqt."
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="unique_product_name_per_category"
            )
        ]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        """
        Maqsad:
        - Agar kitchen_name bo‘sh bo‘lsa, avtomatik ravishda name ni kitchen_name ga yozish.

        Nega kerak:
        - Har safar kitchen_name ni qo‘lda yozish shart bo‘lmaydi
        - Oshxona uchun nom bo‘sh qolib ketmaydi
        """
        if not self.kitchen_name:
            self.kitchen_name = self.name

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class StockIn(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_ins")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            return super().save(*args, **kwargs)  # update bo‘lsa tegmaymiz

        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=self.product.id)

            product.quantity += self.quantity
            product.last_price = self.price
            product.save()

            super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        # mahsulotni yangilash
        self.product.quantity += self.quantity
        self.product.last_price = self.price
        self.product.save()

        super().save(*args, **kwargs)



class StockOut(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_outs")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        # tekshiruv
        if self.product.quantity < self.quantity:
            raise ValueError("Omborda yetarli mahsulot yo‘q!")

        self.product.quantity -= self.quantity
        self.product.save()

        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.pk:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=self.product.id)

            if product.quantity < self.quantity:
                raise ValidationError("Yetarli mahsulot yo‘q!")

            product.quantity -= self.quantity
            product.save()

            super().save(*args, **kwargs)