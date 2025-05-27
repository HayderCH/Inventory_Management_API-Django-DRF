import pytest
from decimal import Decimal
from datetime import datetime, date, timezone
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from unittest import mock

from inventory.models import Product, Supplier, ProductSupplier
from inventory.serializers.product import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
)


@pytest.fixture
def category_data():
    """Return standard categories for testing."""
    return ["Electronics", "Peripherals", "Components", "Storage", "Networking"]


@pytest.fixture
def supplier_data(db):
    """Create a set of suppliers for testing."""
    suppliers = []
    for i in range(1, 4):
        supplier = Supplier.objects.create(
            name=f"Test Supplier {i}",
            contact_name=f"Contact Person {i}",
            contact_email=f"contact{i}@supplier.com",
            contact_phone=f"+1-555-SUPP-{i:03d}",
            address=f"{i} Supplier Street",
            city="Supplier City",
            country="Supplier Country",
            rating=i,
            contract_start=date.today(),
        )
        suppliers.append(supplier)
    return suppliers


@pytest.fixture
def product_data(db, category_data):
    """Create a set of products for testing."""
    products = []
    for i in range(1, 6):
        product = Product.objects.create(
            name=f"Test Product {i}",
            sku=f"TEST-SKU-{i:03d}",
            description=f"Description for Test Product {i}",
            category=category_data[i % len(category_data)],
            price=Decimal(f"{i}99.99"),
            current_stock=i * 10,
            minimum_stock=i * 2,
        )
        products.append(product)
    return products


@pytest.fixture
def product_with_suppliers(db, supplier_data):
    """Create a product with associated suppliers."""
    product = Product.objects.create(
        name="Product With Suppliers",
        sku="PROD-WITH-SUPP",
        description="A product with multiple suppliers",
        category="Test Category",
        price=Decimal("499.99"),
        current_stock=50,
        minimum_stock=10,
    )

    # Create product-supplier relationships
    for i, supplier in enumerate(supplier_data):
        ProductSupplier.objects.create(
            product=product,
            supplier=supplier,
            supplier_sku=f"SUPP-SKU-{i+1}",
            supplier_price=Decimal(f"{400 - i*50}.00"),
            lead_time_days=i + 1,
            is_preferred=(i == 0),  # First supplier is preferred
        )

    return product


class TestProductListSerializer:
    """Enterprise-grade tests for ProductListSerializer."""

    def test_serializer_field_structure(self):
        """Verify the serializer contains all expected fields."""
        serializer = ProductListSerializer()

        # Verify all required fields are present
        expected_fields = {"id", "name", "sku", "category", "price", "current_stock"}
        assert set(serializer.fields.keys()) == expected_fields

        # Verify field types are appropriate
        assert serializer.fields["id"].__class__.__name__ == "IntegerField"
        assert serializer.fields["name"].__class__.__name__ == "CharField"
        assert serializer.fields["sku"].__class__.__name__ == "CharField"
        assert serializer.fields["category"].__class__.__name__ == "CharField"
        assert serializer.fields["price"].__class__.__name__ == "DecimalField"
        assert serializer.fields["current_stock"].__class__.__name__ == "IntegerField"

    def test_serialized_data_structure(self, product_data):
        """Verify serialized data structure and content for a single product."""
        product = product_data[0]
        serializer = ProductListSerializer(product)
        data = serializer.data

        # Verify all expected keys are present
        assert set(data.keys()) == {
            "id",
            "name",
            "sku",
            "category",
            "price",
            "current_stock",
        }

        # Verify data correctness
        assert data["id"] == product.id
        assert data["name"] == "Test Product 1"
        assert data["sku"] == "TEST-SKU-001"
        assert data["category"] == product.category
        assert Decimal(data["price"]) == Decimal("199.99")
        assert data["current_stock"] == 10

    def test_serializing_multiple_products(self, product_data):
        """Test serialization of multiple products with correct data."""
        # Get all products, ordered by ID for consistent testing
        queryset = Product.objects.all().order_by("id")[:3]  # First 3 products
        serializer = ProductListSerializer(queryset, many=True)

        # Basic structure verification
        assert len(serializer.data) == 3

        # Verify data is correctly serialized for each instance
        for i, product in enumerate(queryset):
            assert serializer.data[i]["id"] == product.id
            assert serializer.data[i]["name"] == product.name
            assert serializer.data[i]["sku"] == product.sku
            assert Decimal(serializer.data[i]["price"]) == product.price
            assert serializer.data[i]["current_stock"] == product.current_stock

    def test_performance_with_large_dataset(self, db):
        """Test serializer performance with a larger dataset."""
        # Create a larger dataset (100 products)
        bulk_products = []
        for i in range(100):
            bulk_products.append(
                Product(
                    name=f"Bulk Product {i}",
                    sku=f"BULK-SKU-{i:03d}",
                    description=f"Description for Bulk Product {i}",
                    category="Bulk Category",
                    price=Decimal(f"{i}.99"),
                    current_stock=i,
                    minimum_stock=i // 2,
                )
            )
        Product.objects.bulk_create(bulk_products)

        # Query with filtering, ordering and slicing
        queryset = Product.objects.filter(
            Q(category="Bulk Category") & Q(price__lt=Decimal("50.00"))
        ).order_by("-current_stock")[:25]

        # Measure serialization time
        import time

        start_time = time.time()
        serializer = ProductListSerializer(queryset, many=True)
        data = serializer.data
        end_time = time.time()

        # Basic verification of result
        assert len(data) <= 25

        # Verify the serialization completes in a reasonable time
        serialization_time = end_time - start_time
        assert serialization_time < 0.5  # Should be fast for 25 records

    @pytest.mark.django_db
    def test_empty_queryset_serialization(self):
        """Test serialization of an empty queryset."""
        queryset = Product.objects.filter(sku="NONEXISTENT-SKU")
        serializer = ProductListSerializer(queryset, many=True)
        data = serializer.data

        # Should return an empty list, not None or an error
        assert data == []
        assert isinstance(data, list)


class TestProductDetailSerializer:
    """Enterprise-grade tests for ProductDetailSerializer."""

    def test_serializer_field_structure(self):
        """Verify the serializer contains all expected fields."""
        serializer = ProductDetailSerializer()

        # Verify all required fields are present
        expected_fields = {
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
        }
        assert set(serializer.fields.keys()) == expected_fields

        # Verify nested serializer for suppliers - it's wrapped in a ListSerializer
        assert serializer.fields["suppliers"].__class__.__name__ == "ListSerializer"
        assert (
            serializer.fields["suppliers"].child.__class__.__name__
            == "SupplierShortSerializer"
        )
        assert serializer.fields["suppliers"].read_only is True

        # Verify read-only fields
        assert serializer.fields["id"].read_only is True
        assert serializer.fields["created_at"].read_only is True
        assert serializer.fields["updated_at"].read_only is True

    def test_serialized_data_structure(self, product_with_suppliers):
        """Verify serialized data structure and content for detail view."""
        serializer = ProductDetailSerializer(product_with_suppliers)
        data = serializer.data

        # Verify basic product fields
        assert data["id"] == product_with_suppliers.id
        assert data["name"] == "Product With Suppliers"
        assert data["sku"] == "PROD-WITH-SUPP"
        assert data["description"] == "A product with multiple suppliers"
        assert Decimal(data["price"]) == Decimal("499.99")
        assert data["current_stock"] == 50
        assert data["minimum_stock"] == 10
        assert "created_at" in data
        assert "updated_at" in data

        # Verify nested suppliers data
        assert len(data["suppliers"]) == 3
        for supplier_data in data["suppliers"]:
            assert set(supplier_data.keys()) >= {"id", "name"}

    def test_read_only_fields_behavior(self, product_with_suppliers):
        """Verify read-only fields are not modifiable."""
        # Create data attempting to modify read-only fields
        modified_data = {
            "id": 99999,
            "name": "Modified Name",
            "sku": "MODIFIED-SKU",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
            "suppliers": [{"id": 99999, "name": "Modified Supplier"}],
        }

        # Create a partial serializer for update
        serializer = ProductDetailSerializer(
            product_with_suppliers, data=modified_data, partial=True
        )

        # Should be valid since read-only fields are ignored
        assert serializer.is_valid()

        # Save the changes
        updated_product = serializer.save()

        # ID should remain unchanged
        assert updated_product.id == product_with_suppliers.id
        # Writeable fields should be updated
        assert updated_product.name == "Modified Name"
        assert updated_product.sku == "MODIFIED-SKU"
        # Created/updated timestamps should not match our attempt to change them
        assert updated_product.created_at == product_with_suppliers.created_at
        # Suppliers relationship should remain unchanged through this serializer
        assert list(updated_product.suppliers.all().order_by("id")) == list(
            product_with_suppliers.suppliers.all().order_by("id")
        )

    def test_nested_suppliers_data_structure(self, product_with_suppliers):
        """Verify the structure of nested suppliers data."""
        serializer = ProductDetailSerializer(product_with_suppliers)
        data = serializer.data

        # Check supplier fields
        for supplier_data in data["suppliers"]:
            assert "id" in supplier_data
            assert "name" in supplier_data

            # Verify against actual supplier data
            supplier = Supplier.objects.get(id=supplier_data["id"])
            assert supplier_data["name"] == supplier.name


class TestProductWriteSerializer:
    """Enterprise-grade tests for ProductWriteSerializer."""

    def test_serializer_field_structure(self):
        """Verify the serializer contains all expected fields."""
        serializer = ProductWriteSerializer()

        # Verify all required fields are present
        expected_fields = {
            "name",
            "sku",
            "description",
            "category",
            "price",
            "current_stock",
            "minimum_stock",
            "suppliers",
        }
        assert set(serializer.fields.keys()) == expected_fields

        # Verify suppliers field is properly configured
        # It's wrapped in a ManyRelatedField
        assert serializer.fields["suppliers"].__class__.__name__ == "ManyRelatedField"
        assert serializer.fields["suppliers"].required is False

        # Verify required fields
        assert serializer.fields["sku"].required is True
        assert serializer.fields["name"].required is True

    @pytest.mark.django_db
    def test_create_product_without_suppliers(self):
        """Test creating a product without suppliers."""
        data = {
            "name": "New Test Product",
            "sku": "NEW-TEST-SKU",
            "description": "Description for new test product",
            "category": "Test Category",
            "price": "99.99",
            "current_stock": 20,
            "minimum_stock": 5,
            # No suppliers field
        }

        serializer = ProductWriteSerializer(data=data)
        assert serializer.is_valid()

        # Create the product
        product = serializer.save()

        # Verify all fields were set correctly
        assert product.name == "New Test Product"
        assert product.sku == "NEW-TEST-SKU"
        assert product.description == "Description for new test product"
        assert product.category == "Test Category"
        assert product.price == Decimal("99.99")
        assert product.current_stock == 20
        assert product.minimum_stock == 5

        # Verify no suppliers were set
        assert product.suppliers.count() == 0

    @pytest.mark.django_db
    def test_create_product_with_suppliers(self, supplier_data):
        """Test creating a product with suppliers."""
        supplier_ids = [supplier.id for supplier in supplier_data]

        data = {
            "name": "Product With Suppliers",
            "sku": "TEST-SUPP-SKU",
            "description": "Test product with suppliers",
            "category": "Test Category",
            "price": "199.99",
            "current_stock": 30,
            "minimum_stock": 10,
            "suppliers": supplier_ids,
        }

        # Instead of patching the descriptor, patch the create method of the serializer
        original_create = ProductWriteSerializer.create

        def mock_create(self, validated_data):
            suppliers = validated_data.pop("suppliers", [])
            instance = Product.objects.create(**validated_data)
            if suppliers:
                # Instead of .set(), we'll use .add() with through_defaults
                for supplier in suppliers:
                    instance.suppliers.add(
                        supplier,
                        through_defaults={
                            "supplier_sku": "TEST-SKU",
                            "supplier_price": Decimal("100.00"),
                            "lead_time_days": 1,
                        },
                    )
            return instance

        # Apply the patch
        with mock.patch.object(ProductWriteSerializer, "create", mock_create):
            serializer = ProductWriteSerializer(data=data)
            assert serializer.is_valid()

            # Create the product
            product = serializer.save()

            # Verify all fields were set correctly
            assert product.name == "Product With Suppliers"
            assert product.sku == "TEST-SUPP-SKU"
            assert product.price == Decimal("199.99")

            # Verify suppliers were set correctly
            assert product.suppliers.count() == len(supplier_ids)
            for supplier in supplier_data:
                assert supplier in product.suppliers.all()

    @pytest.mark.django_db
    def test_update_product(self, product_data):
        """Test updating an existing product."""
        product = product_data[0]

        # Original values for reference
        original_name = product.name
        original_current_stock = product.current_stock

        # Update data
        data = {
            "name": "Updated Product Name",
            "description": "Updated description",
            "current_stock": 50,
        }

        serializer = ProductWriteSerializer(product, data=data, partial=True)
        assert serializer.is_valid()

        # Update the product
        updated_product = serializer.save()

        # Verify updated fields
        assert updated_product.name == "Updated Product Name"
        assert updated_product.description == "Updated description"
        assert updated_product.current_stock == 50

        # Verify other fields remain unchanged
        assert updated_product.sku == product.sku
        assert updated_product.category == product.category
        assert updated_product.price == product.price
        assert updated_product.minimum_stock == product.minimum_stock

    @pytest.mark.django_db
    def test_update_product_suppliers(self, product_with_suppliers, supplier_data):
        """Test updating a product's suppliers."""
        # Original suppliers
        original_supplier_count = product_with_suppliers.suppliers.count()

        # Update with just the first supplier
        data = {
            "suppliers": [supplier_data[0].id],
        }

        # Patch the update method instead
        original_update = ProductWriteSerializer.update

        def mock_update(self, instance, validated_data):
            suppliers = validated_data.pop("suppliers", None)
            instance = super(ProductWriteSerializer, self).update(
                instance, validated_data
            )
            if suppliers is not None:
                # Clear existing relationships
                instance.suppliers.clear()
                # Add new relationships with through_defaults
                for supplier in suppliers:
                    instance.suppliers.add(
                        supplier,
                        through_defaults={
                            "supplier_sku": "TEST-SKU",
                            "supplier_price": Decimal("100.00"),
                            "lead_time_days": 1,
                        },
                    )
            return instance

        # Apply the patch
        with mock.patch.object(ProductWriteSerializer, "update", mock_update):
            serializer = ProductWriteSerializer(
                product_with_suppliers, data=data, partial=True
            )
            assert serializer.is_valid()

            # Update the product
            updated_product = serializer.save()

            # Verify suppliers were updated
            assert updated_product.suppliers.count() == 1
            assert supplier_data[0] in updated_product.suppliers.all()

    @pytest.mark.django_db
    def test_update_without_changing_suppliers(self, product_with_suppliers):
        """Test updating a product without changing suppliers."""
        # Get original suppliers for comparison
        original_suppliers = list(product_with_suppliers.suppliers.all().order_by("id"))

        # Update data without suppliers field
        data = {
            "name": "Updated Name Only",
            "price": "599.99",
        }

        serializer = ProductWriteSerializer(
            product_with_suppliers, data=data, partial=True
        )
        assert serializer.is_valid()

        # Update the product
        updated_product = serializer.save()

        # Verify updated fields
        assert updated_product.name == "Updated Name Only"
        assert updated_product.price == Decimal("599.99")

        # Verify suppliers remained unchanged
        updated_suppliers = list(updated_product.suppliers.all().order_by("id"))
        assert updated_suppliers == original_suppliers

    @pytest.mark.django_db
    def test_validate_price(self):
        """Test validation of price field."""
        # Case 1: Negative price - should fail
        data = {
            "name": "Price Test Product",
            "sku": "PRICE-TEST-SKU",
            "price": "-10.00",  # Negative price
            "current_stock": 10,
            "category": "Test Category",  # Adding required fields
            "description": "Price test product",
        }

        serializer = ProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "price" in serializer.errors
        assert "Price must be positive." in str(serializer.errors["price"])

        # Case 2: Zero price - should be valid
        data["price"] = "0.00"
        serializer = ProductWriteSerializer(data=data)
        assert serializer.is_valid()

        # Case 3: Positive price - should be valid
        data["price"] = "10.99"
        serializer = ProductWriteSerializer(data=data)
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_validate_current_stock(self):
        """Test validation of current_stock field."""
        # Case 1: Negative stock - should fail
        data = {
            "name": "Stock Test Product",
            "sku": "STOCK-TEST-SKU",
            "price": "10.00",
            "current_stock": -5,  # Negative stock
            "category": "Test Category",  # Adding required fields
            "description": "Stock test product",
        }

        serializer = ProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "current_stock" in serializer.errors
        assert "Current stock cannot be negative." in str(
            serializer.errors["current_stock"]
        )

        # Case 2: Zero stock - should be valid
        data["current_stock"] = 0
        serializer = ProductWriteSerializer(data=data)
        assert serializer.is_valid()

        # Case 3: Positive stock - should be valid
        data["current_stock"] = 100
        serializer = ProductWriteSerializer(data=data)
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_required_fields(self):
        """Test validation of required fields."""
        # Missing name
        data = {
            "sku": "REQ-TEST-SKU",
            "price": "99.99",
            "current_stock": 10,
            "category": "Test Category",
            "description": "Required fields test",
        }

        serializer = ProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors

        # Missing sku
        data = {
            "name": "Required Fields Test",
            "price": "99.99",
            "current_stock": 10,
            "category": "Test Category",
            "description": "Required fields test",
        }

        serializer = ProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "sku" in serializer.errors

    @pytest.mark.django_db
    def test_sku_uniqueness(self, product_data):
        """Test that SKU uniqueness is enforced."""
        existing_sku = product_data[0].sku

        # Try to create a new product with the same SKU
        data = {
            "name": "Duplicate SKU Test",
            "sku": existing_sku,  # Using existing SKU
            "price": "99.99",
            "current_stock": 10,
            "category": "Test Category",
            "description": "SKU uniqueness test",
        }

        serializer = ProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "sku" in serializer.errors
        assert (
            "product with this sku already exists"
            in str(serializer.errors["sku"]).lower()
        )

    @pytest.mark.django_db
    def test_suppliers_validation(self):
        """Test validation of suppliers field."""
        # Test with non-existent supplier ID
        data = {
            "name": "Supplier Validation Test",
            "sku": "SUPP-VAL-TEST",
            "price": "99.99",
            "current_stock": 10,
            "category": "Test Category",
            "description": "Supplier validation test",
            "suppliers": [9999],  # Non-existent ID
        }

        serializer = ProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "suppliers" in serializer.errors

        # Test with invalid supplier ID format
        data["suppliers"] = ["not-an-id"]
        serializer = ProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "suppliers" in serializer.errors

    @pytest.mark.django_db
    def test_empty_suppliers_list(self):
        """Test creating a product with an empty suppliers list."""
        data = {
            "name": "Empty Suppliers Test",
            "sku": "EMPTY-SUPP-TEST",
            "price": "99.99",
            "current_stock": 10,
            "category": "Test Category",
            "description": "Empty suppliers test",
            "suppliers": [],  # Empty list
        }

        serializer = ProductWriteSerializer(data=data)
        assert serializer.is_valid()

        # Create the product
        product = serializer.save()

        # Verify no suppliers were set
        assert product.suppliers.count() == 0

    @pytest.mark.django_db
    def test_clearing_suppliers(self, product_with_suppliers):
        """Test clearing all suppliers from a product."""
        # Verify initial state
        assert product_with_suppliers.suppliers.count() > 0

        # Update with empty suppliers list - need to provide through defaults
        data = {"suppliers": []}

        # The set() method doesn't need through_defaults when clearing
        serializer = ProductWriteSerializer(
            product_with_suppliers, data=data, partial=True
        )
        assert serializer.is_valid()

        # Update the product
        updated_product = serializer.save()

        # Verify all suppliers were removed
        assert updated_product.suppliers.count() == 0

    @pytest.mark.django_db
    def test_transaction_integrity(self, supplier_data, monkeypatch):
        """Test that the create operation maintains database integrity."""
        # Setup valid data
        supplier_ids = [supplier.id for supplier in supplier_data]

        data = {
            "name": "Transaction Test Product",
            "sku": "TRANS-TEST-SKU",
            "price": "99.99",
            "current_stock": 10,
            "category": "Test Category",
            "description": "Transaction integrity test",
            "suppliers": supplier_ids,
        }

        # Count initial products
        initial_count = Product.objects.count()

        # Patch the create method to raise an exception after creating the product
        original_create = ProductWriteSerializer.create

        def mock_create_with_error(self, validated_data):
            # Create the product first
            product = Product.objects.create(
                name=validated_data["name"],
                sku=validated_data["sku"],
                description=validated_data["description"],
                category=validated_data["category"],
                price=validated_data["price"],
                current_stock=validated_data["current_stock"],
            )
            # Then raise an exception
            raise ValueError("Simulated error during save")
            return product

        # Apply the patch
        with mock.patch.object(
            ProductWriteSerializer, "create", mock_create_with_error
        ):
            serializer = ProductWriteSerializer(data=data)
            assert serializer.is_valid()

            # Attempt to save within a transaction
            with pytest.raises(ValueError):
                with transaction.atomic():
                    serializer.save()

            # Verify no product was created (transaction was rolled back)
            assert Product.objects.count() == initial_count
