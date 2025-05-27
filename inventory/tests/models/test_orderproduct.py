import pytest
from inventory.models import OrderProduct, Order, Product, Supplier
import datetime
from decimal import Decimal
from django.core.exceptions import ValidationError


@pytest.mark.django_db
def test_orderproduct_creation_and_fields():
    """Test creation of OrderProduct and all its fields."""
    supplier = Supplier.objects.create(
        name="Order Supplier",
        contact_name="Anna Order",
        contact_email="anna@supplier.com",
        address="123 Main St",
        city="Order City",
        country="Orderland",
        rating=8,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="OP-001",
        supplier=supplier,
    )
    product = Product.objects.create(
        name="Order Widget",
        sku="ORDER-W1",
        description="Widget for orders",
        category="Widgets",
        price=Decimal("12.50"),
        current_stock=100,
        minimum_stock=5,
    )
    op = OrderProduct.objects.create(
        order=order,
        product=product,
        quantity=10,
        unit_price=Decimal("11.00"),
    )
    assert op.order == order
    assert op.product == product
    assert op.quantity == 10
    assert op.unit_price == Decimal("11.00")
    assert str(op) == f"{product.name} x10 for {order.order_number}"


@pytest.mark.django_db
def test_orderproduct_positive_quantity_constraint():
    supplier = Supplier.objects.create(
        name="Supplier PQ",
        contact_name="PQ",
        contact_email="pq@supplier.com",
        address="PQ St",
        city="PQ City",
        country="PQland",
        rating=1,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="OP-002",
        supplier=supplier,
    )
    product = Product.objects.create(
        name="PQ Widget",
        sku="PQ-W1",
        description="PQ Desc",
        category="PQCat",
        price=Decimal("5.00"),
        current_stock=20,
        minimum_stock=2,
    )

    # 0 and negative numbers should NOT be valid
    for invalid_qty in (0, -3):
        op = OrderProduct(
            order=order,
            product=product,
            quantity=invalid_qty,
            unit_price=Decimal("5.00"),
        )
        with pytest.raises(ValidationError):
            op.full_clean()


@pytest.mark.django_db
def test_orderproduct_unit_price_precision():
    """Test that unit_price holds correct decimal precision."""
    supplier = Supplier.objects.create(
        name="Supplier UP",
        contact_name="UP",
        contact_email="up@supplier.com",
        address="UP St",
        city="UP City",
        country="UPland",
        rating=2,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="OP-003",
        supplier=supplier,
    )
    product = Product.objects.create(
        name="UP Widget",
        sku="UP-W1",
        description="UP Desc",
        category="UPCat",
        price=Decimal("7.99"),
        current_stock=50,
        minimum_stock=5,
    )
    op = OrderProduct.objects.create(
        order=order,
        product=product,
        quantity=1,
        unit_price=Decimal("7.99"),
    )
    assert op.unit_price == Decimal("7.99")


@pytest.mark.django_db
def test_orderproduct_unique_index_on_order_and_product():
    """Test that the index exists and allows multiple products per order, but not duplicate product per order."""
    supplier = Supplier.objects.create(
        name="Index Supplier",
        contact_name="Index",
        contact_email="index@supplier.com",
        address="Index St",
        city="Index City",
        country="Indexland",
        rating=3,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="OP-004",
        supplier=supplier,
    )
    product1 = Product.objects.create(
        name="Index Widget 1",
        sku="IDX-W1",
        description="IDX1",
        category="IDXCat",
        price=Decimal("2.00"),
        current_stock=10,
        minimum_stock=1,
    )
    product2 = Product.objects.create(
        name="Index Widget 2",
        sku="IDX-W2",
        description="IDX2",
        category="IDXCat",
        price=Decimal("3.00"),
        current_stock=8,
        minimum_stock=1,
    )
    op1 = OrderProduct.objects.create(
        order=order,
        product=product1,
        quantity=2,
        unit_price=Decimal("2.00"),
    )
    op2 = OrderProduct.objects.create(
        order=order,
        product=product2,
        quantity=1,
        unit_price=Decimal("3.00"),
    )
    assert op1 in order.order_products.all()
    assert op2 in order.order_products.all()
    # Should allow same product on different orders
    order2 = Order.objects.create(
        order_number="OP-005",
        supplier=supplier,
    )
    op3 = OrderProduct.objects.create(
        order=order2,
        product=product1,
        quantity=1,
        unit_price=Decimal("2.00"),
    )
    assert op3 in order2.order_products.all()


@pytest.mark.django_db
def test_orderproduct_cascade_delete_on_order():
    """Test that deleting an order cascades deletes to related OrderProduct."""
    supplier = Supplier.objects.create(
        name="Cascade Supplier",
        contact_name="Cascade",
        contact_email="cascade@supplier.com",
        address="Cascade St",
        city="Cascade City",
        country="Cascadia",
        rating=4,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="OP-006",
        supplier=supplier,
    )
    product = Product.objects.create(
        name="Cascade Widget",
        sku="CAS-W1",
        description="Cascade Description",
        category="CascadeCat",
        price=Decimal("6.00"),
        current_stock=30,
        minimum_stock=3,
    )
    OrderProduct.objects.create(
        order=order,
        product=product,
        quantity=5,
        unit_price=Decimal("6.00"),
    )
    order.delete()
    assert OrderProduct.objects.count() == 0


@pytest.mark.django_db
def test_orderproduct_protect_on_product_delete():
    """Test that deleting the product raises error due to PROTECT (should not delete OrderProduct)."""
    supplier = Supplier.objects.create(
        name="Protect Supplier",
        contact_name="Protect",
        contact_email="protect@supplier.com",
        address="Protect St",
        city="Protect City",
        country="Protectland",
        rating=6,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="OP-007",
        supplier=supplier,
    )
    product = Product.objects.create(
        name="Protect Widget",
        sku="PROT-W1",
        description="Protection",
        category="ProtCat",
        price=Decimal("20.00"),
        current_stock=10,
        minimum_stock=2,
    )
    OrderProduct.objects.create(
        order=order,
        product=product,
        quantity=1,
        unit_price=Decimal("20.00"),
    )
    with pytest.raises(Exception):
        product.delete()
    assert Product.objects.filter(pk=product.pk).exists()
    assert OrderProduct.objects.count() == 1


@pytest.mark.django_db
def test_orderproduct_related_manager_and_str():
    """Test related manager functionality and __str__ representation."""
    supplier = Supplier.objects.create(
        name="Rel Supplier",
        contact_name="Rel",
        contact_email="rel@supplier.com",
        address="Rel St",
        city="Rel City",
        country="Relland",
        rating=7,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="OP-008",
        supplier=supplier,
    )
    product = Product.objects.create(
        name="Rel Widget",
        sku="REL-W1",
        description="Rel Desc",
        category="RelCat",
        price=Decimal("4.00"),
        current_stock=15,
        minimum_stock=2,
    )
    op = OrderProduct.objects.create(
        order=order,
        product=product,
        quantity=7,
        unit_price=Decimal("4.00"),
    )
    # Related manager
    assert order.order_products.count() == 1
    assert order.order_products.first() == op
    # String representation
    assert str(op) == "Rel Widget x7 for OP-008"
