from rest_framework import serializers
from .models import Table, Category, Product, StockOut, StockIn


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = [
            "id",
            "name",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Stol nomi bo‘sh bo‘lishi mumkin emas.")
        return value


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Kategoriya nomi bo‘sh bo‘lishi mumkin emas.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "kitchen_name",
            "price",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "category_name",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Mahsulot nomi bo‘sh bo‘lishi mumkin emas.")
        return value

    def validate_kitchen_name(self, value):
        value = value.strip()
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo‘lishi mumkin emas.")
        return value

    def validate(self, attrs):
        """
        kitchen_name bo‘sh kelishi mumkin.
        Bunday holatda model save ichida avtomatik name dan olinadi.
        """
        name = attrs.get("name")
        kitchen_name = attrs.get("kitchen_name", "")

        if name:
            attrs["name"] = name.strip()

        if kitchen_name is not None:
            attrs["kitchen_name"] = kitchen_name.strip()

        return attrs




class ProductMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price", "is_active"]


class CategoryMenuSerializer(serializers.ModelSerializer):
    products = ProductMenuSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "products"]



class ProductFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "price",
            "is_active",
            "kitchen_name",
        ]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Nom bo‘sh bo‘lmasin")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo‘lmaydi")
        return value



class StockInSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockIn
        fields = "__all__"
        read_only_fields = ["created_at", "created_by"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class StockOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockOut
        fields = "__all__"
        read_only_fields = ["created_at", "created_by"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)