import pytest
from decimal import Decimal
from django.db import IntegrityError
from inventory.models import Product, Location, StockLevel, Supplier
import datetime


@pytest.mark.django_db
def test_stocklevel_creation_and_str():
    """Test creation of StockLevel and its string representation."""
    product = Product.objects.create(
        name="Test Widget",
        sku="WIDG-001",
        description="Test desc",
        category="TestCat",
        price=Decimal("10.00"),
        current_stock=100,
        minimum_stock=10,
    )
    location = Location.objects.create(
        name="Main Warehouse",
        code="MW-001",
        address="123 Main St",
        city="Metropolis",
        country="Freedonia",
    )
    stock = StockLevel.objects.create(
        product=product,
        location=location,
        quantity=50,
    )
    assert stock.product == product
    assert stock.location == location
    assert stock.quantity == 50
    assert str(stock) == f"{product.name} @ {location.code}: 50"


@pytest.mark.django_db
def test_unique_constraint_on_product_and_location():
    """Test that StockLevel enforces uniqueness for product/location."""
    product = Product.objects.create(
        name="Unique Widget",
        sku="UNIQ-001",
        description="Unique desc",
        category="UniqueCat",
        price=Decimal("15.00"),
        current_stock=20,
        minimum_stock=3,
    )
    location = Location.objects.create(
        name="Secondary Warehouse",
        code="SW-001",
        address="456 Side St",
        city="Smallville",
        country="Freedonia",
    )
    StockLevel.objects.create(
        product=product,
        location=location,
        quantity=5,
    )
    # Second insert with same product/location should fail
    with pytest.raises(IntegrityError):
        StockLevel.objects.create(
            product=product,
            location=location,
            quantity=7,
        )


@pytest.mark.django_db
def test_stocklevel_quantity_can_be_negative_or_zero():
    """Test that StockLevel allows zero or negative quantity (e.g., for oversell situations)."""
    product = Product.objects.create(
        name="Negative Widget",
        sku="NEG-001",
        description="Negative desc",
        category="NegCat",
        price=Decimal("7.50"),
        current_stock=0,
        minimum_stock=0,
    )
    location = Location.objects.create(
        name="Overflow Shed",
        code="OF-001",
        address="Overflow St",
        city="Overflowville",
        country="Freedonia",
    )
    zero_stock = StockLevel.objects.create(
        product=product,
        location=location,
        quantity=0,
    )
    negative_stock = StockLevel.objects.create(
        product=product,
        location=Location.objects.create(
            name="Shortage Branch",
            code="SB-001",
            address="Shortage Blvd",
            city="Shortage City",
            country="Freedonia",
        ),
        quantity=-10,
    )
    assert zero_stock.quantity == 0
    assert negative_stock.quantity == -10


@pytest.mark.django_db
def test_cascade_delete_product_also_deletes_stocklevels():
    """Test that deleting a product deletes its StockLevel(s)."""
    product = Product.objects.create(
        name="Cascade Widget",
        sku="CAS-001",
        description="Cascade desc",
        category="CascadeCat",
        price=Decimal("12.00"),
        current_stock=6,
        minimum_stock=1,
    )
    location = Location.objects.create(
        name="Cascade WH",
        code="CAS-WH",
        address="Cascade St",
        city="Cascade City",
        country="Freedonia",
    )
    StockLevel.objects.create(
        product=product,
        location=location,
        quantity=8,
    )
    product.delete()
    assert StockLevel.objects.count() == 0


@pytest.mark.django_db
def test_cascade_delete_location_also_deletes_stocklevels():
    """Test that deleting a location deletes its StockLevel(s)."""
    product = Product.objects.create(
        name="Delete Loc Widget",
        sku="DELLOC-001",
        description="Del Loc desc",
        category="DelLocCat",
        price=Decimal("9.00"),
        current_stock=4,
        minimum_stock=1,
    )
    location = Location.objects.create(
        name="Delete Me",
        code="DELLOC-001",
        address="Nowhere",
        city="NoCity",
        country="NoCountry",
    )
    StockLevel.objects.create(
        product=product,
        location=location,
        quantity=2,
    )
    location.delete()
    assert StockLevel.objects.count() == 0
