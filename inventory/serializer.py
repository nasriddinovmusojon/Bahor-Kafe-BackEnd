from rest_framework import serializers
from .models import Ingredient, Recipe, Dish, StockMovement


class IngredientSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    unit_name = serializers.CharField(source="unit.name", read_only=True)

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "quantity",
            "min_quantity",
            "unit_name",
            "status",
            "branch"
        ]

    def get_status(self, obj):
        if obj.quantity <= obj.min_quantity:
            return {
                "type": "LOW",
                "label": "⚠️ Past qoldiq"
            }
        return {
            "type": "OK",
            "label": "OK"
        }

class RecipeSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    unit = serializers.CharField(source='ingredient.unit.name', read_only=True)

    class Meta:
        model = Recipe
        fields = ['ingredient', 'ingredient_name', 'unit', 'quantity']


class DishSerializer(serializers.ModelSerializer):
    recipes = RecipeSerializer(many=True)

    class Meta:
        model = Dish
        fields = ['id', 'name', 'recipes']

    def create(self, validated_data):
        recipes_data = validated_data.pop('recipes')
        dish = Dish.objects.create(**validated_data)

        for recipe in recipes_data:
            Recipe.objects.create(dish=dish, **recipe)

        return dish



class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ['id', 'ingredient', 'type', 'quantity', 'reason', 'created_by', 'created_at']