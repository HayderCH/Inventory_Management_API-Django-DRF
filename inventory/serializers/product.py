from rest_framework import serializers
from ..models import Product, Supplier
from .short_serializers import SupplierShortSerializer


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "sku", "category", "price", "current_stock"]


class ProductDetailSerializer(serializers.ModelSerializer):

    suppliers = SupplierShortSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "description",
            "category",
            "price",
            "current_stock",
            "minimum_stock",
            "created_at",
            "updated_at",
            "suppliers",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductWriteSerializer(serializers.ModelSerializer):
    suppliers = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Supplier.objects.all(), required=False
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "description",
            "category",
            "price",
            "current_stock",
            "minimum_stock",
            "suppliers",
        ]
        extra_kwargs = {
            "sku": {"required": True},
            "name": {"required": True},
        }

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

    def validate_current_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Current stock cannot be negative.")
        return value

    def create(self, validated_data):
        suppliers = validated_data.pop("suppliers", [])
        product = super().create(validated_data)
        if suppliers:
            product.suppliers.set(suppliers)
        return product

    def update(self, instance, validated_data):
        suppliers = validated_data.pop("suppliers", None)
        product = super().update(instance, validated_data)
        if suppliers is not None:
            product.suppliers.set(suppliers)
        return product
