from django.db import models
from django.contrib.auth import get_user_model

from table.models import Product

User = get_user_model()


class Unit(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=255)

    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    branch = models.ForeignKey('sozlamalar.Branch', on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    TYPE = (
        ('IN', 'Kirim'),
        ('OUT', 'Chiqim'),
        ('SALE', 'Sotuv'),
    )

    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    type = models.CharField(max_length=10, choices=TYPE)

    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



class Recipe(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recipes")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="recipe_items")
    quantity = models.FloatField()  # nechta ingredient ketadi

    def __str__(self):
        return f"{self.product.name} -> {self.ingredient.name} ({self.quantity})"


class Dish(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
