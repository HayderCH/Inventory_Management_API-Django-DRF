from rest_framework import serializers
from ..models import StockTransfer, Product, Location
from .short_serializers import (
    ProductShortSerializer,
    LocationShortSerializer,
    UserShortSerializer,
)


class StockTransferListSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    from_location = LocationShortSerializer(read_only=True)
    to_location = LocationShortSerializer(read_only=True)
    requested_by = UserShortSerializer(read_only=True)
    approved_by = UserShortSerializer(read_only=True)

    class Meta:
        model = StockTransfer
        fields = [
            "id",
            "product",
            "from_location",
            "to_location",
            "quantity",
            "status",
            "reason",
            "requested_by",
            "approved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class StockTransferDetailSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    from_location = LocationShortSerializer(read_only=True)
    to_location = LocationShortSerializer(read_only=True)
    requested_by = UserShortSerializer(read_only=True)
    approved_by = UserShortSerializer(read_only=True)

    class Meta:
        model = StockTransfer
        fields = [
            "id",
            "product",
            "from_location",
            "to_location",
            "quantity",
            "status",
            "reason",
            "requested_by",
            "approved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class StockTransferWriteSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    from_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    to_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())

    class Meta:
        model = StockTransfer
        fields = [
            "product",
            "from_location",
            "to_location",
            "quantity",
            "reason",
        ]

    def validate(self, data):
        if data.get("quantity", 0) <= 0:
            raise serializers.ValidationError(
                {"quantity": "Quantity must be greater than zero."}
            )
        if data.get("from_location") == data.get("to_location"):
            raise serializers.ValidationError(
                {"to_location": "Source and destination locations must be different"}
            )
