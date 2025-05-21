from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
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
    contract_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    rating = models.IntegerField(default=0)
    contract_start = models.DateField(blank=True)
    contract_end = models.DateField(blank=True)
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
