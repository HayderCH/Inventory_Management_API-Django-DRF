import pytest
from inventory.models import Order, Supplier, Product, OrderProduct
import datetime
from decimal import Decimal


@pytest.mark.django_db
def test_order_creation_and_fields():
    """
    Test creation of an Order and check all its fields and string representation.
    """
    supplier = Supplier.objects.create(
        name="Test Supplier",
        contact_name="Jane Smith",
        contact_email="jane@supplier.com",
        address="1 Test St",
        city="Testville",
        country="Testland",
        rating=5,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="ORD-001",
        supplier=supplier,
        status="pending",
    )
    assert order.order_number == "ORD-001"
    assert order.supplier == supplier
    assert order.status == "pending"
    assert order.created_at is not None
    assert order.updated_at is not None
    assert str(order) == f"Order ORD-001 from {supplier} (pending)"


@pytest.mark.django_db
def test_order_status_choices_and_defaults():
    """
    Test that Order status choices work and default is 'pending'.
    """
    supplier = Supplier.objects.create(
        name="Status Supplier",
        contact_name="Sam Status",
        contact_email="status@supplier.com",
        address="2 Status Ave",
        city="Statustown",
        country="Statusland",
        rating=4,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="ORD-002",
        supplier=supplier,
    )
    assert order.status == "pending"
    # Test all valid statuses
    for status in ["approved", "shipped", "received", "canceled"]:
        order.status = status
        order.save()
        order.refresh_from_db()
        assert order.status == status


@pytest.mark.django_db
def test_order_unique_order_number_constraint():
    """
    Test that order_number must be unique.
    """
    supplier = Supplier.objects.create(
        name="Unique Supplier",
        contact_name="Unique Name",
        contact_email="unique@supplier.com",
        address="3 Unique Rd",
        city="Uniquecity",
        country="Uniqueland",
        rating=3,
        contract_start=datetime.date.today(),
    )
    Order.objects.create(order_number="ORD-003", supplier=supplier)
    with pytest.raises(Exception):
        Order.objects.create(order_number="ORD-003", supplier=supplier)


@pytest.mark.django_db
def test_order_update_and_timestamps():
    """
    Test that updating an order updates the updated_at timestamp.
    """
    supplier = Supplier.objects.create(
        name="Timestamp Supplier",
        contact_name="Tim Stamps",
        contact_email="tim@supplier.com",
        address="4 Stamp St",
        city="Stamptown",
        country="Stampland",
        rating=2,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="ORD-004",
        supplier=supplier,
    )
    updated_at_before = order.updated_at
    order.status = "approved"
    order.save()
    order.refresh_from_db()
    assert order.updated_at > updated_at_before
    assert order.status == "approved"


@pytest.mark.django_db
def test_order_supplier_protect_delete():
    """
    Test that deleting a supplier with orders raises error due to PROTECT.
    """
    supplier = Supplier.objects.create(
        name="Protect Supplier",
        contact_name="Protecty",
        contact_email="protect@supplier.com",
        address="5 Protect Blvd",
        city="Protectville",
        country="Protectland",
        rating=10,
        contract_start=datetime.date.today(),
    )
    Order.objects.create(order_number="ORD-005", supplier=supplier)
    with pytest.raises(Exception):
        supplier.delete()
    assert Supplier.objects.filter(pk=supplier.pk).exists()


@pytest.mark.django_db
def test_order_orderproduct_relationship_and_str():
    """
    Test creating OrderProduct and their relationship to Order and Product.
    """
    supplier = Supplier.objects.create(
        name="OP Supplier",
        contact_name="Opal",
        contact_email="opal@supplier.com",
        address="6 Opal St",
        city="Opalville",
        country="Opalland",
        rating=7,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="ORD-006",
        supplier=supplier,
    )
    product1 = Product.objects.create(
        name="Prod1",
        sku="P1",
        description="Product 1",
        category="Cat1",
        price=Decimal("10.00"),
        current_stock=10,
        minimum_stock=1,
    )
    product2 = Product.objects.create(
        name="Prod2",
        sku="P2",
        description="Product 2",
        category="Cat2",
        price=Decimal("15.00"),
        current_stock=5,
        minimum_stock=1,
    )
    op1 = OrderProduct.objects.create(
        order=order, product=product1, quantity=2, unit_price=Decimal("10.00")
    )
    op2 = OrderProduct.objects.create(
        order=order, product=product2, quantity=1, unit_price=Decimal("15.00")
    )
    assert op1.order == order
    assert op1.product == product1
    assert op1.quantity == 2
    assert op1.unit_price == Decimal("10.00")
    assert str(op1) == f"{product1.name} x2 for {order.order_number}"

    assert op2.order == order
    assert op2.product == product2
    assert op2.quantity == 1
    assert op2.unit_price == Decimal("15.00")
    assert str(op2) == f"{product2.name} x1 for {order.order_number}"

    # Check related manager
    order_products = order.order_products.all()
    assert set(order_products) == {op1, op2}


@pytest.mark.django_db
def test_order_deletion_cascades_to_orderproducts():
    """
    Test that deleting an order cascades to its OrderProduct entries.
    """
    supplier = Supplier.objects.create(
        name="Cascade Supplier",
        contact_name="Cascade",
        contact_email="cascade@supplier.com",
        address="7 Cascade Ave",
        city="Cascadia",
        country="CascadeLand",
        rating=6,
        contract_start=datetime.date.today(),
    )
    order = Order.objects.create(
        order_number="ORD-007",
        supplier=supplier,
    )
    product = Product.objects.create(
        name="Cascade Prod",
        sku="CP1",
        description="Cascade Product",
        category="Cascades",
        price=Decimal("8.00"),
        current_stock=15,
        minimum_stock=2,
    )
    OrderProduct.objects.create(
        order=order, product=product, quantity=3, unit_price=Decimal("8.00")
    )
    order.delete()
    assert OrderProduct.objects.count() == 0
