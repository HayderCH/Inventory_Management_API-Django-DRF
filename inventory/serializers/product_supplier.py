from rest_framework import serializers
from ..models import ProductSupplier, Location
from .short_serializers import ProductShortSerializer, SupplierShortSerializer


class ProductSupplierListSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    supplier = SupplierShortSerializer(read_only=True)

    class Meta:
        model = ProductSupplier
        fields = [
            "id",
            "product",  # nested
            "supplier",  # nested
            "supplier_sku",
            "supplier_price",
            "lead_time_days",
            "contract_start",
            "contract_end",
            "is_preferred",
        ]


class ProductSupplierDetailSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer(read_only=True)
    supplier = SupplierShortSerializer(read_only=True)

    class Meta:
        model = ProductSupplier
        fields = [
            "id",
            "product",
            "supplier",
            "supplier_sku",
            "supplier_price",
            "lead_time_days",
            "contract_start",
            "contract_end",
            "is_preferred",
        ]


class ProductSupplierWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSupplier
        fields = [
            "product",
            "supplier",
            "supplier_sku",
            "supplier_price",
            "lead_time_days",
            "contract_start",
            "contract_end",
            "is_preferred",
        ]

    def validate(self, attrs):
        # unique together check
        product = attrs.get("product")
        supplier = attrs.get("supplier")
        if (
            product
            and supplier
            and ProductSupplier.objects.filter(product=product, supplier=supplier)
            .exclude(pk=self.instance.pk if self.instance else None)
            .exists()
        ):
            raise serializers.ValidationError(
                "This product-supplier relationship already exists."
            )
        # contract date logic
        contract_start = attrs.get("contract_start")
        contract_end = attrs.get("contract_end")
        if contract_start and contract_end and contract_end < contract_start:
            raise serializers.ValidationError("Contract cannot end before it starts.")
        return attrs

    def validate_supplier_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Supplier price must be positive.")
        return value

    def validate_lead_time_days(self, value):
        if value < 0:
            raise serializers.ValidationError("Lead time must be non-negative.")
        return value


class LocationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "code",
            "city",
            "country",
            "updated_at",
        ]
        read_only_fields = fields
