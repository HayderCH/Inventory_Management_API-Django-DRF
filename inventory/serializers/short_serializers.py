from rest_framework import serializers
from ..models import Location, Supplier, Product, StockTransfer
from django.contrib.auth import get_user_model


class LocationShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "name", "code")


class SupplierShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "contact_name"]


class ProductShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "sku"]


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "first_name", "last_name")


class StockTransferShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransfer
        fields = ("id", "product", "from_location", "to_location", "quantity", "status")
