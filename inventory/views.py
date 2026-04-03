from rest_framework.viewsets import ModelViewSet
from .models import Ingredient, Recipe, Dish, StockMovement
from .serializer import IngredientSerializer, RecipeSerializer, DishSerializer
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from decimal import Decimal
from rest_framework.exceptions import ValidationError


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.filter(is_active=True)
    serializer_class = IngredientSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


class DishViewSet(viewsets.ModelViewSet):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer

    # 🔥 OVQAT ISHLATISH (OMBORDAN KAMAYTIRISH)
    @action(detail=True, methods=['post'])
    def cook(self, request, pk=None):
        count = int(request.data.get("count", 1))  # nechta ovqat

        dish = self.get_object()

        # tekshirish
        for recipe in dish.recipes.all():
            kerak = recipe.amount * count
            if recipe.ingredient.quantity < kerak:
                raise ValidationError(f"{recipe.ingredient.name} yetarli emas!")

        # kamaytirish
        for recipe in dish.recipes.all():
            ingredient = recipe.ingredient
            ingredient.quantity -= recipe.amount * count
            ingredient.save()

        return Response({"message": "Ombordan ayrildi ✅"})

