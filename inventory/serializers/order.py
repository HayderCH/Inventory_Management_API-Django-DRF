from rest_framework import serializers
from ..models import Order, OrderProduct
from .short_serializers import SupplierShortSerializer
from .order_product import OrderProductNestedSerializer, OrderProductWriteSerializer


class OrderListSerializer(serializers.ModelSerializer):
    supplier = SupplierShortSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "supplier",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    supplier = SupplierShortSerializer(read_only=True)
    order_products = OrderProductNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "supplier",
            "status",
            "created_at",
            "updated_at",
            "order_products",
        ]
        read_only_fields = fields


class OrderWriteSerializer(serializers.ModelSerializer):
    order_products = OrderProductWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            "order_number",
            "supplier",
            "status",
            "order_products",
        ]
        extra_kwargs = {
            "order_number": {"required": True},
            "supplier": {"required": True},
        }

    def validate_order_number(self, value):
        value = value.upper()
        if not value.isalnum():
            raise serializers.ValidationError("Order number must be alphanumeric.")
        qs = Order.objects.filter(order_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Order number already exists.")
        return value

    def create(self, validated_data):
        order_products_data = validated_data.pop("order_products", [])
        order = super().create(validated_data)
        for item in order_products_data:
            OrderProduct.objects.create(order=order, **item)
        return order

    def update(self, instance, validated_data):
        order_products_data = validated_data.pop("order_products", None)
        instance = super().update(instance, validated_data)
        if order_products_data is not None:
            instance.order_products.all().delete()
            for item in order_products_data:
                OrderProduct.objects.create(order=instance, **item)
        return instance
