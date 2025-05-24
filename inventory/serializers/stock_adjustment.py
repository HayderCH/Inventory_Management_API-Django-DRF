from rest_framework import serializers
from ..models import StockAdjustment, Product, Location, StockTransfer
from .short_serializers import (
    ProductShortSerializer,
    LocationShortSerializer,
    StockTransferShortSerializer,
    UserShortSerializer,
)


class StockAdjustmentListSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    location = LocationShortSerializer(read_only=True)
    stock_transfer = StockTransferShortSerializer(read_only=True)
    adjusted_by = UserShortSerializer(read_only=True)

    class Meta:
        model = StockAdjustment
        fields = (
            "id",
            "product",
            "location",
            "quantity",
            "adjustment_type",
            "reason",
            "stock_transfer",
            "adjusted_by",
            "created_at",
        )
        read_only_fields = fields


class StockAdjustmentDetailSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    location = LocationShortSerializer(read_only=True)
    stock_transfer = StockTransferShortSerializer(read_only=True)
    adjusted_by = UserShortSerializer(read_only=True)

    class Meta:
        model = StockAdjustment
        fields = (
            "id",
            "product",
            "location",
            "quantity",
            "adjustment_type",
            "reason",
            "stock_transfer",
            "adjusted_by",
            "created_at",
        )
        read_only_fields = fields


class StockAdjustmentWriteSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    stock_transfer = serializers.PrimaryKeyRelatedField(
        queryset=StockTransfer.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = StockAdjustment
        fields = (
            "product",
            "location",
            "quantity",
            "adjustment_type",
            "reason",
            "stock_transfer",
        )

    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity adjustment cannot be 0.")
        return value

    def validate(self, attrs):
        adjustment_type = attrs.get("adjustment_type")
        stock_transfer = attrs.get("stock_transfer")
        if (
            adjustment_type
            and adjustment_type.startswith("transfer")
            and not stock_transfer
        ):
            raise serializers.ValidationError(
                "Stock transfer must be provided for transfer adjustments."
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return StockAdjustment.objects.create(adjusted_by=user, **validated_data)
