from rest_framework import serializers
from .models import Branch, CheckSettings, TaxSettings, OrderFlowSettings, RestaurantSettings


class BranchSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id',
            'name',
            'city',
            'cash_desk_count',
            'kitchen_count',
            'is_active',
            'status'
        ]

    def get_status(self, obj):
        return "Faol" if obj.is_active else "Nofaol"


class CheckSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckSettings
        fields = "__all__"


class TaxSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxSettings
        fields = '__all__'


class OrderFlowSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderFlowSettings
        fields = "__all__"


class RestaurantSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantSettings
        fields = '__all__'