from rest_framework import serializers
from ..models import StockLevel
from .short_serializers import ProductShortSerializer
from .location import LocationListSerializer


class StockLevelListSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    location = LocationListSerializer(read_only=True)

    class Meta:
        model = StockLevel
        fields = [
            "id",
            "product",
            "location",
            "quantity",
            "updated_at",
        ]
        read_only_fields = fields


class StockLevelDetailSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    location = LocationListSerializer(read_only=True)

    class Meta:
        model = StockLevel
        fields = [
            "id",
            "product",
            "location",
            "quantity",
            "updated_at",
        ]
        read_only_fields = fields


class StockLevelWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLevel
        fields = [
            "product",
            "location",
            "quantity",
        ]

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value

    def validate(self, attrs):
        # Ensure unique together constraint at the serializer level for early feedback
        product = attrs.get("product")
        location = attrs.get("location")
        if product and location:
            qs = StockLevel.objects.filter(product=product, location=location)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Stock level for this product at this location already exists."
                )
        return attrs
