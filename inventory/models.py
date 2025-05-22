from django.db import models
from django.conf import settings


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    suppliers = models.ManyToManyField(
        "Supplier", through="ProductSupplier", related_name="products"
    )

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    rating = models.IntegerField(default=0, db_index=True)
    contract_start = models.DateField(blank=True)
    contract_end = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class ProductSupplier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    supplier_sku = models.CharField(max_length=100)
    supplier_price = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time_days = models.IntegerField(default=0)
    contract_start = models.DateField(blank=True, null=True)
    contract_end = models.DateField(blank=True, null=True)
    is_preferred = models.BooleanField(default=False)

    class Meta:
        unique_together = ("product", "supplier")

    def __str__(self):
        return f"{self.product} from {self.supplier}"


class Location(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    country = models.CharField(max_length=100, blank=True, db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Order(models.Model):
    order_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey("Supplier", on_delete=models.PROTECT)
    status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("shipped", "Shipped"),
            ("received", "Received"),
            ("canceled", "Canceled"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number} from {self.supplier} ({self.status})"


class OrderProduct(models.Model):
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, related_name="order_products"
    )
    product = models.ForeignKey("Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} for {self.order.order_number}"


class StockLevel(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    location = models.ForeignKey("Location", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "location")

    def __str__(self):
        return f"{self.product.name} @ {self.location.code}: {self.quantity}"


class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = [
        ("receive", "Receive"),
        ("remove", "Remove"),
        ("correct", "Correct"),
        ("audit", "Audit"),
        ("loss", "Loss"),
        ("transfer_in", "Transfer In"),
        ("transfer_out", "Transfer Out"),
    ]

    product = models.ForeignKey("Product", on_delete=models.PROTECT)
    location = models.ForeignKey("Location", on_delete=models.PROTECT)
    quantity = models.IntegerField()
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    reason = models.CharField(max_length=255, blank=True)
    stock_transfer = models.ForeignKey(
        "StockTransfer", null=True, blank=True, on_delete=models.SET_NULL
    )
    adjusted_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.adjustment_type} {self.quantity} {self.product.name} @ {self.location.code}"


class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
    ]

    product = models.ForeignKey("Product", on_delete=models.PROTECT)
    from_location = models.ForeignKey(
        "Location", related_name="transfers_out", on_delete=models.PROTECT
    )
    to_location = models.ForeignKey(
        "Location", related_name="transfers_in", on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reason = models.CharField(max_length=255, blank=True)
    requested_by = models.ForeignKey(
        "auth.User", related_name="transfers_requested", on_delete=models.PROTECT
    )
    approved_by = models.ForeignKey(
        "auth.User",
        related_name="transfers_approved",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transfer {self.product.name} {self.quantity} {self.from_location.code}->{self.to_location.code} ({self.status})"


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=50)
    object_id = models.PositiveBigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    extra = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.object_type} {self.object_id} at {self.timestamp}"
