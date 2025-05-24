from datetime import datetime
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    AuditLog,
    Location,
    Order,
    OrderProduct,
    Product,
    ProductSupplier,
    StockAdjustment,
    StockLevel,
    StockTransfer,
    Supplier,
)

User = get_user_model()


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


class LocationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "code",
            "address",
            "city",
            "country",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class LocationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "name",
            "code",
            "address",
            "city",
            "country",
            "notes",
        ]

    def validate_code(self, value):
        value = value.upper()
        if not value.isalnum():
            raise serializers.ValidationError("Code must be alphanumeric.")
        qs = Location.objects.filter(code=value)
        if self.instance:  # On update, exclude self
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A location with this code already exists."
            )
        return value


#  --- orderProduct through model serializers


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


#  --- order serializers ---


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


class AuditLogListSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action",
            "object_type",
            "object_id",
            "timestamp",
            "extra",
        ]
        read_only_fields = fields


class AuditLogDetailSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action",
            "object_type",
            "object_id",
            "timestamp",
            "extra",
        ]
        read_only_fields = fields
