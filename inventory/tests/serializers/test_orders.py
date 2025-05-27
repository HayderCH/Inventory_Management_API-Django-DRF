import pytest
from decimal import Decimal
from django.utils import timezone
from unittest import mock

from inventory.models import Product, Supplier, Order, OrderProduct
from inventory.serializers.order import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderWriteSerializer,
)


@pytest.fixture
def supplier(db):
    return Supplier.objects.create(
        name="Test Supplier",
        contact_name="Contact Person",
        contact_email="contact@supplier.com",
        address="123 Supplier St",
        city="Supplier City",
        country="Supplier Country",
        contract_start="2025-01-01",
    )


@pytest.fixture
def second_supplier(db):
    return Supplier.objects.create(
        name="Second Supplier",
        contact_name="Another Contact",
        contact_email="another@supplier.com",
        address="456 Supplier Ave",
        city="Another City",
        country="Another Country",
        contract_start="2025-02-01",
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Test Product",
        sku="TEST-SKU-001",
        description="Test product description",
        category="Test Category",
        price=Decimal("99.99"),
        current_stock=100,
        minimum_stock=10,
    )


@pytest.fixture
def another_product(db):
    return Product.objects.create(
        name="Another Product",
        sku="TEST-SKU-002",
        description="Another test product description",
        category="Test Category",
        price=Decimal("199.99"),
        current_stock=50,
        minimum_stock=5,
    )


@pytest.fixture
def order(db, supplier):
    return Order.objects.create(
        order_number="ORD001",
        supplier=supplier,
        status="pending",
    )


@pytest.fixture
def order_with_products(db, supplier, product, another_product):
    order = Order.objects.create(
        order_number="ORD002",
        supplier=supplier,
        status="approved",
    )
    OrderProduct.objects.create(
        order=order,
        product=product,
        quantity=5,
        unit_price=Decimal("89.99"),
    )
    OrderProduct.objects.create(
        order=order,
        product=another_product,
        quantity=3,
        unit_price=Decimal("189.99"),
    )
    return order


class TestOrderListSerializer:
    """Enterprise-grade tests for OrderListSerializer"""

    def test_serializer_field_structure(self):
        """Test that serializer has the expected field structure"""
        serializer = OrderListSerializer()

        # Verify fields and their types
        assert "id" in serializer.fields
        assert "order_number" in serializer.fields
        assert "supplier" in serializer.fields
        assert "status" in serializer.fields
        assert "created_at" in serializer.fields
        assert "updated_at" in serializer.fields

        # Verify nested serializer for supplier
        assert (
            serializer.fields["supplier"].__class__.__name__
            == "SupplierShortSerializer"
        )

    def test_all_fields_are_read_only(self):
        """Verify that all fields in OrderListSerializer are marked as read-only"""
        serializer = OrderListSerializer()

        # Check each field to ensure it's read-only
        for field_name, field in serializer.fields.items():
            assert field.read_only, f"Field '{field_name}' should be read-only"

    def test_serializer_output_structure(self, order):
        """Test that serialized data has the expected structure"""
        serializer = OrderListSerializer(order)
        data = serializer.data

        # Verify output structure
        assert set(data.keys()) == {
            "id",
            "order_number",
            "supplier",
            "status",
            "created_at",
            "updated_at",
        }
        # Updated to match the actual fields in SupplierShortSerializer
        assert set(data["supplier"].keys()) == {"id", "name", "contact_name"}

    def test_serializer_data_matches_model_instance(self, order):
        """Test that serialized data matches the model instance"""
        serializer = OrderListSerializer(order)
        data = serializer.data

        # Check data values
        assert data["id"] == order.id
        assert data["order_number"] == order.order_number
        assert data["status"] == order.status
        assert data["supplier"]["id"] == order.supplier.id
        assert data["supplier"]["name"] == order.supplier.name
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_serialization_of_multiple_orders(self, order, supplier):
        """Test serializing multiple orders correctly"""
        # Create a second order
        second_order = Order.objects.create(
            order_number="ORD003",
            supplier=supplier,
            status="shipped",
        )

        # Serialize multiple orders
        orders = Order.objects.all().order_by("id")
        serializer = OrderListSerializer(orders, many=True)
        data = serializer.data

        # Verify results
        assert len(data) == 2
        assert data[0]["id"] == order.id
        assert data[0]["order_number"] == order.order_number
        assert data[1]["id"] == second_order.id
        assert data[1]["order_number"] == second_order.order_number

    def test_read_only_operations(self, order, supplier):
        """Test that read-only operations do not modify data"""
        # Get original values
        original_order_number = order.order_number
        original_status = order.status

        # Attempt to update through the read-only serializer
        modified_data = {
            "id": 9999,
            "order_number": "CHANGED-ORD001",
            "supplier": {"id": supplier.id, "name": "Changed Supplier Name"},
            "status": "shipped",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
        }

        serializer = OrderListSerializer(order, data=modified_data)
        # Should still be valid because fields are read-only
        assert serializer.is_valid()

        # Saving should not modify the instance
        updated_order = serializer.save()

        # Verify original values are preserved
        assert updated_order.order_number == original_order_number
        assert updated_order.status == original_status


class TestOrderDetailSerializer:
    """Enterprise-grade tests for OrderDetailSerializer"""

    def test_serializer_field_structure(self):
        """Test that serializer has the expected field structure"""
        serializer = OrderDetailSerializer()

        # Verify fields and their types
        assert "id" in serializer.fields
        assert "order_number" in serializer.fields
        assert "supplier" in serializer.fields
        assert "status" in serializer.fields
        assert "created_at" in serializer.fields
        assert "updated_at" in serializer.fields
        assert "order_products" in serializer.fields

        # Verify nested serializers
        assert (
            serializer.fields["supplier"].__class__.__name__
            == "SupplierShortSerializer"
        )
        # The ListSerializer wraps the OrderProductNestedSerializer
        assert (
            serializer.fields["order_products"].child.__class__.__name__
            == "OrderProductNestedSerializer"
        )

    def test_all_fields_are_read_only(self):
        """Verify that all fields in OrderDetailSerializer are marked as read-only"""
        serializer = OrderDetailSerializer()

        # Check each field to ensure it's read-only
        for field_name, field in serializer.fields.items():
            assert field.read_only, f"Field '{field_name}' should be read-only"

    def test_serializer_output_structure(self, order_with_products):
        """Test that serialized data has the expected structure"""
        serializer = OrderDetailSerializer(order_with_products)
        data = serializer.data

        # Verify output structure
        assert set(data.keys()) == {
            "id",
            "order_number",
            "supplier",
            "status",
            "created_at",
            "updated_at",
            "order_products",
        }
        # Updated to match the actual fields in SupplierShortSerializer
        assert set(data["supplier"].keys()) == {"id", "name", "contact_name"}
        assert len(data["order_products"]) == 2
        assert set(data["order_products"][0].keys()) == {
            "id",
            "product",
            "quantity",
            "unit_price",
        }

    def test_serializer_data_matches_model_instance(self, order_with_products):
        """Test that serialized data matches the model instance"""
        serializer = OrderDetailSerializer(order_with_products)
        data = serializer.data

        # Check basic order fields
        assert data["id"] == order_with_products.id
        assert data["order_number"] == order_with_products.order_number
        assert data["status"] == order_with_products.status
        assert data["supplier"]["id"] == order_with_products.supplier.id
        assert data["supplier"]["name"] == order_with_products.supplier.name

        # Check nested order products
        order_products = list(order_with_products.order_products.all().order_by("id"))
        assert len(data["order_products"]) == 2

        for i, op in enumerate(order_products):
            assert data["order_products"][i]["id"] == op.id
            assert data["order_products"][i]["quantity"] == op.quantity
            assert Decimal(data["order_products"][i]["unit_price"]) == op.unit_price
            assert data["order_products"][i]["product"]["id"] == op.product.id
            assert data["order_products"][i]["product"]["name"] == op.product.name

    def test_read_only_operations(self, order_with_products):
        """Test that read-only operations do not modify data"""
        # Get original values
        original_order_number = order_with_products.order_number
        original_status = order_with_products.status
        original_product_count = order_with_products.order_products.count()

        # Attempt to update through the read-only serializer
        modified_data = {
            "id": 9999,
            "order_number": "CHANGED-ORD002",
            "supplier": {"id": 9999, "name": "Changed Supplier"},
            "status": "canceled",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
            "order_products": [
                {
                    "id": 9999,
                    "product": {
                        "id": 9999,
                        "name": "Changed Product",
                        "sku": "CHANGED-SKU",
                    },
                    "quantity": 999,
                    "unit_price": "999.99",
                }
            ],
        }

        serializer = OrderDetailSerializer(order_with_products, data=modified_data)
        # Should still be valid because fields are read-only
        assert serializer.is_valid()

        # Saving should not modify the instance
        updated_order = serializer.save()

        # Verify original values are preserved
        assert updated_order.order_number == original_order_number
        assert updated_order.status == original_status
        assert updated_order.order_products.count() == original_product_count


class TestOrderWriteSerializer:
    """Enterprise-grade tests for OrderWriteSerializer"""

    def test_serializer_field_structure(self):
        """Test that serializer has the expected field structure"""
        serializer = OrderWriteSerializer()

        # Verify fields exist
        assert "order_number" in serializer.fields
        assert "supplier" in serializer.fields
        assert "status" in serializer.fields
        assert "order_products" in serializer.fields

        # Verify nested serializer for order_products
        # The ListSerializer wraps the actual serializer
        assert (
            serializer.fields["order_products"].child.__class__.__name__
            == "OrderProductWriteSerializer"
        )
        assert serializer.fields["order_products"].write_only is True

    @pytest.mark.django_db
    def test_required_fields(self):
        """Test that required fields are properly enforced"""
        # Empty data
        serializer = OrderWriteSerializer(data={})
        assert not serializer.is_valid()
        assert "order_number" in serializer.errors
        assert "supplier" in serializer.errors

        # Missing supplier
        serializer = OrderWriteSerializer(data={"order_number": "ORD123"})
        assert not serializer.is_valid()
        assert "supplier" in serializer.errors

        # Missing order_number
        serializer = OrderWriteSerializer(data={"supplier": 1})
        assert not serializer.is_valid()
        assert "order_number" in serializer.errors

    @pytest.mark.django_db
    def test_validate_order_number_uppercase(self, supplier):
        """Test that order number is converted to uppercase"""
        data = {
            "order_number": "ord123",
            "supplier": supplier.id,
            "status": "pending",
            "order_products": [],
        }

        serializer = OrderWriteSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["order_number"] == "ORD123"

    @pytest.mark.django_db
    def test_validate_order_number_alphanumeric(self, supplier):
        """Test validation for non-alphanumeric order number"""
        data = {
            "order_number": "ORD-123",  # Contains a dash
            "supplier": supplier.id,
            "status": "pending",
            "order_products": [],
        }

        serializer = OrderWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "order_number" in serializer.errors
        assert "Order number must be alphanumeric." in str(
            serializer.errors["order_number"]
        )

    @pytest.mark.django_db
    def test_validate_order_number_uniqueness(self, order, supplier):
        """Test validation for duplicate order number"""
        data = {
            "order_number": order.order_number,  # Already exists
            "supplier": supplier.id,
            "status": "pending",
            "order_products": [],
        }

        serializer = OrderWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "order_number" in serializer.errors
        # Fixed to match the actual error message
        assert "order with this order number already exists" in str(
            serializer.errors["order_number"]
        )

    @pytest.mark.django_db
    def test_validate_order_number_uniqueness_for_update(self, order, supplier):
        """Test that order number uniqueness validation allows the same number for the same instance"""
        data = {
            "order_number": order.order_number,  # Same as current
            "supplier": supplier.id,
            "status": "shipped",  # Changed status
            "order_products": [],
        }

        serializer = OrderWriteSerializer(order, data=data)
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_create_order_with_products(self, supplier, product, another_product):
        """Test creating an order with nested order products"""
        data = {
            "order_number": "ORD123",
            "supplier": supplier.id,
            "status": "pending",
            "order_products": [
                {"product": product.id, "quantity": 5, "unit_price": "99.99"},
                {"product": another_product.id, "quantity": 3, "unit_price": "189.99"},
            ],
        }

        serializer = OrderWriteSerializer(data=data)
        assert serializer.is_valid()

        # Create the order
        order = serializer.save()

        # Verify order fields
        assert order.order_number == "ORD123"
        assert order.supplier == supplier
        assert order.status == "pending"

        # Verify order products
        order_products = order.order_products.all()
        assert order_products.count() == 2
        product_ids = [op.product.id for op in order_products]
        assert product.id in product_ids
        assert another_product.id in product_ids

        # Verify specific order product details
        op1 = order_products.get(product=product)
        assert op1.quantity == 5
        assert op1.unit_price == Decimal("99.99")

        op2 = order_products.get(product=another_product)
        assert op2.quantity == 3
        assert op2.unit_price == Decimal("189.99")

    @pytest.mark.django_db
    def test_update_order_with_products(
        self, order_with_products, second_supplier, product
    ):
        """Test updating an order with nested order products"""
        # Initial product count
        initial_product_count = order_with_products.order_products.count()
        assert initial_product_count == 2

        # We need a unique order number for the update to pass validation
        data = {
            "order_number": "UPDATEDORD002",  # Must be unique
            "supplier": second_supplier.id,
            "status": "shipped",
            "order_products": [
                {"product": product.id, "quantity": 10, "unit_price": "79.99"}
            ],
        }

        serializer = OrderWriteSerializer(order_with_products, data=data)
        assert serializer.is_valid()

        # Update the order
        updated_order = serializer.save()

        # Verify order fields
        assert updated_order.order_number == "UPDATEDORD002"
        assert updated_order.supplier == second_supplier
        assert updated_order.status == "shipped"

        # Verify order products were replaced
        order_products = updated_order.order_products.all()
        assert order_products.count() == 1  # Now only one product

        # Verify the new order product
        op = order_products.first()
        assert op.product == product
        assert op.quantity == 10
        assert op.unit_price == Decimal("79.99")

    @pytest.mark.django_db
    def test_update_order_without_order_products(
        self, order_with_products, second_supplier
    ):
        """Test updating an order without changing order products"""
        # Initial product count
        initial_product_count = order_with_products.order_products.count()
        initial_product_ids = set(
            op.id for op in order_with_products.order_products.all()
        )

        # We need a unique order number for the update to pass validation
        data = {
            "order_number": "UPDATEDORD002",  # Must be unique
            "supplier": second_supplier.id,
            "status": "shipped",
            # No order_products field
        }

        serializer = OrderWriteSerializer(order_with_products, data=data, partial=True)
        assert serializer.is_valid()

        # Update the order
        updated_order = serializer.save()

        # Verify order fields
        assert updated_order.order_number == "UPDATEDORD002"
        assert updated_order.supplier == second_supplier
        assert updated_order.status == "shipped"

        # Verify order products were NOT changed
        assert updated_order.order_products.count() == initial_product_count
        current_product_ids = set(op.id for op in updated_order.order_products.all())
        assert current_product_ids == initial_product_ids

    @pytest.mark.django_db
    def test_create_order_with_invalid_products(self, supplier, product):
        """Test that creating an order with invalid products fails validation"""
        data = {
            "order_number": "ORD123",
            "supplier": supplier.id,
            "status": "pending",
            "order_products": [
                {
                    "product": product.id,
                    "quantity": -5,  # Invalid negative quantity
                    "unit_price": "99.99",
                }
            ],
        }

        serializer = OrderWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "order_products" in serializer.errors

    @pytest.mark.django_db
    def test_update_order_with_invalid_products(
        self, order_with_products, supplier, product
    ):
        """Test that updating an order with invalid products fails validation"""
        data = {
            "order_number": "UPDATEDORD002",
            "supplier": supplier.id,
            "status": "shipped",
            "order_products": [
                {
                    "product": product.id,
                    "quantity": 0,  # Invalid zero quantity
                    "unit_price": "99.99",
                }
            ],
        }

        serializer = OrderWriteSerializer(order_with_products, data=data)
        assert not serializer.is_valid()
        assert "order_products" in serializer.errors

    @pytest.mark.django_db
    def test_create_with_empty_order_products(self, supplier):
        """Test creating an order with empty order_products list"""
        data = {
            "order_number": "ORD123",
            "supplier": supplier.id,
            "status": "pending",
            "order_products": [],
        }

        serializer = OrderWriteSerializer(data=data)
        assert serializer.is_valid()

        order = serializer.save()
        assert order.order_number == "ORD123"
        assert order.supplier == supplier
        assert order.status == "pending"
        assert order.order_products.count() == 0
