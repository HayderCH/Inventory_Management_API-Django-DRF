from django.contrib import admin
from .models import (
    Product,
    Supplier,
    ProductSupplier,
    Location,
    Order,
    OrderProduct,
    StockLevel,
    StockAdjustment,
    StockTransfer,
    AuditLog,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "price",
        "current_stock",
        "minimum_stock",
        "updated_at",
    )
    search_fields = ("name", "sku", "category")
    list_filter = ("category",)
    # Removed filter_horizontal due to custom through model on suppliers


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "contact_name",
        "contact_email",
        "city",
        "country",
        "rating",
        "contract_start",
        "contract_end",
        "updated_at",
    )
    search_fields = ("name", "contact_name", "contact_email", "city", "country")
    list_filter = ("country", "rating")


@admin.register(ProductSupplier)
class ProductSupplierAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "supplier",
        "supplier_sku",
        "supplier_price",
        "lead_time_days",
        "is_preferred",
        "contract_start",
        "contract_end",
    )
    list_filter = ("is_preferred", "contract_start", "contract_end")
    search_fields = ("product__name", "supplier__name", "supplier_sku")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "city", "country", "updated_at")
    search_fields = ("name", "code", "city", "country")
    list_filter = ("country",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "supplier", "status", "created_at", "updated_at")
    search_fields = ("order_number", "supplier__name")
    list_filter = ("status", "supplier")


@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "unit_price")
    search_fields = ("order__order_number", "product__name")


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "quantity", "updated_at")
    search_fields = ("product__name", "location__name", "location__code")
    list_filter = ("location",)


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "location",
        "quantity",
        "adjustment_type",
        "adjusted_by",
        "created_at",
    )
    search_fields = ("product__name", "location__name", "adjusted_by__username")
    list_filter = ("adjustment_type", "location")


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "from_location",
        "to_location",
        "quantity",
        "status",
        "requested_by",
        "approved_by",
        "created_at",
        "updated_at",
    )
    search_fields = ("product__name", "from_location__name", "to_location__name")
    list_filter = ("status", "from_location", "to_location")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "object_type", "object_id", "timestamp")
    list_filter = ("action", "object_type", "user")
    search_fields = ("object_type", "object_id", "extra")
