from rest_framework import serializers

from .models import Product, ProductSupplier, Supplier


class SupplierShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "contact_name"]


class ProductShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "sku"]


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
        if contract_start and value and value < contract_start:
            raise serializers.ValidationError(
                "Contract end cannot be before its start."
            )
        return value


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