from rest_framework import serializers
from ..models import Supplier
from .product import ProductListSerializer
from datetime import datetime


class SupplierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "contact_name",
            "contact_email",
            "city",
            "country",
            "rating",
        ]


class SupplierDetailSerializer(serializers.ModelSerializer):

    products = ProductListSerializer(many=True, read_only=True, source="products")

    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "contact_name",
            "contact_email",
            "contact_phone",
            "address",
            "city",
            "country",
            "rating",
            "contract_start",
            "contract_end",
            "notes",
            "created_at",
            "updated_at",
            "products",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "products",
        ]


class SupplierWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "name",
            "contact_name",
            "contact_email",
            "contact_phone",
            "address",
            "city",
            "country",
            "rating",
            "contract_start",
            "contract_end",
            "notes",
        ]
        extra_kwargs = {
            "name": {"required": True},
            "contact_name": {"required": True},
            "contact_email": {"required": True},
        }

    def validate_rating(self, value):
        if value < 0 or value > 5:
            raise serializers.ValidationError("Rating must be between 0 and 5.")
        return value

    def validate_contract_end(self, value):
        contract_start = self.initial_data.get("contract_start")
        if contract_start and value:
            if not isinstance(contract_start, (datetime,)):
                try:
                    contract_start = datetime.strptime(
                        contract_start, "%Y-%m-%d"
                    ).date()
                except Exception as exc:
                    raise serializers.ValidationError(
                        "Invalid contract start date format."
                    ) from exc
            if value < contract_start:
                raise serializers.ValidationError(
                    "Contract end cannot be before its start."
                )
        return value
