import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from inventory.models import Product, Supplier, Order, OrderProduct
from inventory.serializers.order_product import (
    OrderProductNestedSerializer,
    OrderProductListSerializer,
    OrderProductDetailSerializer,
    OrderProductWriteSerializer,
)

User = get_user_model()


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
def order(db, supplier):
    return Order.objects.create(
        order_number="ORD-TEST-001", supplier=supplier, status="pending"
    )


@pytest.fixture
def order_product(db, order, product):
    return OrderProduct.objects.create(
        order=order, product=product, quantity=5, unit_price=Decimal("89.99")
    )


class TestOrderProductNestedSerializer:
    def test_serializer_contains_expected_fields(self, order_product):
        """Test that serializer contains the expected fields."""
        serializer = OrderProductNestedSerializer(order_product)
        data = serializer.data

        assert set(data.keys()) == {"id", "product", "quantity", "unit_price"}
        assert set(data["product"].keys()) == {"id", "name", "sku"}

    def test_serializer_data_matches_model_instance(self, order_product):
        """Test that serialized data matches the model instance."""
        serializer = OrderProductNestedSerializer(order_product)
        data = serializer.data

        assert data["id"] == order_product.id
        assert data["quantity"] == order_product.quantity
        assert Decimal(data["unit_price"]) == order_product.unit_price
        assert data["product"]["id"] == order_product.product.id
        assert data["product"]["name"] == order_product.product.name
        assert data["product"]["sku"] == order_product.product.sku


class TestOrderProductListSerializer:
    def test_serializer_contains_expected_fields(self, order_product):
        """Test that serializer contains the expected fields."""
        serializer = OrderProductListSerializer(order_product)
        data = serializer.data

        assert set(data.keys()) == {"id", "product", "quantity", "unit_price"}
        assert set(data["product"].keys()) == {"id", "name", "sku"}

    def test_serializer_data_matches_model_instance(self, order_product):
        """Test that serialized data matches the model instance."""
        serializer = OrderProductListSerializer(order_product)
        data = serializer.data

        assert data["id"] == order_product.id
        assert data["quantity"] == order_product.quantity
        assert Decimal(data["unit_price"]) == order_product.unit_price
        assert data["product"]["id"] == order_product.product.id
        assert data["product"]["name"] == order_product.product.name
        assert data["product"]["sku"] == order_product.product.sku

    def test_serializer_many_items(self, order, product):
        """Test serializer with multiple items."""
        # Create multiple order products
        op1 = OrderProduct.objects.create(
            order=order, product=product, quantity=5, unit_price=Decimal("89.99")
        )

        product2 = Product.objects.create(
            name="Second Product",
            sku="TEST-SKU-002",
            description="Second test product",
            category="Test Category",
            price=Decimal("49.99"),
            current_stock=50,
        )

        op2 = OrderProduct.objects.create(
            order=order, product=product2, quantity=10, unit_price=Decimal("45.99")
        )

        # Test serialization of multiple items
        order_products = OrderProduct.objects.filter(order=order)
        serializer = OrderProductListSerializer(order_products, many=True)
        data = serializer.data

        assert len(data) == 2
        assert data[0]["product"]["name"] == op1.product.name
        assert data[1]["product"]["name"] == op2.product.name


class TestOrderProductDetailSerializer:
    def test_serializer_contains_expected_fields(self, order_product):
        """Test that serializer contains the expected fields."""
        serializer = OrderProductDetailSerializer(order_product)
        data = serializer.data

        assert set(data.keys()) == {"id", "order", "product", "quantity", "unit_price"}
        assert set(data["product"].keys()) == {"id", "name", "sku"}

    def test_serializer_data_matches_model_instance(self, order_product):
        """Test that serialized data matches the model instance."""
        serializer = OrderProductDetailSerializer(order_product)
        data = serializer.data

        assert data["id"] == order_product.id
        assert data["order"] == order_product.order.id
        assert data["quantity"] == order_product.quantity
        assert Decimal(data["unit_price"]) == order_product.unit_price
        assert data["product"]["id"] == order_product.product.id
        assert data["product"]["name"] == order_product.product.name
        assert data["product"]["sku"] == order_product.product.sku


class TestOrderProductWriteSerializer:
    def test_serializer_contains_expected_fields(self, product):
        """Test that serializer contains the expected fields."""
        data = {"product": product.id, "quantity": 5, "unit_price": "99.99"}
        serializer = OrderProductWriteSerializer(data=data)
        assert serializer.is_valid()
        assert set(serializer.validated_data.keys()) == {
            "product",
            "quantity",
            "unit_price",
        }

    def test_create_order_product(self, order, product):
        """Test creating an order product through the serializer."""
        data = {"product": product.id, "quantity": 5, "unit_price": "99.99"}
        serializer = OrderProductWriteSerializer(data=data)
        assert serializer.is_valid()

        order_product = serializer.save(order=order)
        assert order_product.order == order
        assert order_product.product == product
        assert order_product.quantity == 5
        assert order_product.unit_price == Decimal("99.99")

    def test_update_order_product(self, order_product):
        """Test updating an order product through the serializer."""
        data = {
            "product": order_product.product.id,
            "quantity": 10,  # Changed from 5 to 10
            "unit_price": "79.99",  # Changed from 89.99 to 79.99
        }
        serializer = OrderProductWriteSerializer(order_product, data=data)
        assert serializer.is_valid()

        updated_order_product = serializer.save()
        assert updated_order_product.quantity == 10
        assert updated_order_product.unit_price == Decimal("79.99")

    def test_validate_quantity_negative(self, product):
        """Test validation for negative quantity."""
        data = {
            "product": product.id,
            "quantity": -5,  # Negative quantity
            "unit_price": "99.99",
        }
        serializer = OrderProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors
        # Updated assertion to match Django's actual error message
        assert "Ensure this value is greater than or equal to 1." in str(
            serializer.errors["quantity"]
        )

    def test_validate_quantity_zero(self, product):
        """Test validation for zero quantity."""
        data = {
            "product": product.id,
            "quantity": 0,  # Zero quantity
            "unit_price": "99.99",
        }
        serializer = OrderProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors
        # Updated assertion to match Django's actual error message
        assert "Ensure this value is greater than or equal to 1." in str(
            serializer.errors["quantity"]
        )

    def test_validate_unit_price_negative(self, product):
        """Test validation for negative unit price."""
        data = {
            "product": product.id,
            "quantity": 5,
            "unit_price": "-10.00",  # Negative unit price
        }
        serializer = OrderProductWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "unit_price" in serializer.errors
        assert "Unit price must be non-negative." in str(
            serializer.errors["unit_price"]
        )
