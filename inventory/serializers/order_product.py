from rest_framework import serializers
from ..models import OrderProduct
from .short_serializers import ProductShortSerializer


class OrderProductNestedSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)

    class Meta:
        model = OrderProduct
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
        ]

class OrderProductListSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)

    class Meta:
        model = OrderProduct
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
        ]


class OrderProductDetailSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    order = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OrderProduct
        fields = [
            "id",
            "order",
            "product",
            "quantity",
            "unit_price",
        ]


class OrderProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = [
            "product",
            "quantity",
            "unit_price",
        ]
        extra_kwargs = {
            "quantity": {"min_value": 1},
            "unit_price": {"min_value": 0},
        }

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price must be non-negative.")
        return value
