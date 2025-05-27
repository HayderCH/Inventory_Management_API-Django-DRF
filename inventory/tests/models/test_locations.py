import pytest
from inventory.models import Location, StockLevel, Product
from decimal import Decimal


@pytest.mark.django_db
def test_location_creation_and_fields():
    """
    Test creation of a Location and all its fields, including blank and unique.
    """
    location = Location.objects.create(
        name="Main Warehouse",
        code="WH-001",
        address="123 Warehouse Ave",
        city="Warehouseton",
        country="Freedonia",
        notes="Primary storage facility.",
    )
    assert location.name == "Main Warehouse"
    assert location.code == "WH-001"
    assert location.address == "123 Warehouse Ave"
    assert location.city == "Warehouseton"
    assert location.country == "Freedonia"
    assert location.notes == "Primary storage facility."
    assert location.created_at is not None
    assert location.updated_at is not None
    assert str(location) == "Main Warehouse (WH-001)"


@pytest.mark.django_db
def test_location_blank_fields_and_defaults():
    """
    Test blank fields and default values for Location.
    """
    location = Location.objects.create(name="Empty Depot", code="DEP-002")
    assert location.address == ""
    assert location.city == ""
    assert location.country == ""
    assert location.notes == ""


@pytest.mark.django_db
def test_location_code_unique_constraint():
    """
    Test that Location.code must be unique.
    """
    Location.objects.create(name="Warehouse A", code="UNIQ-001")
    with pytest.raises(Exception):
        Location.objects.create(name="Warehouse B", code="UNIQ-001")


@pytest.mark.django_db
def test_location_index_on_city_and_country():
    """
    Test that the city/country index allows querying efficiently.
    """
    # This is more about DB optimization but we can test the field works for filtering
    Location.objects.create(name="Loc1", code="C1", city="Alpha", country="Freedonia")
    Location.objects.create(name="Loc2", code="C2", city="Alpha", country="Freedonia")
    qs = Location.objects.filter(city="Alpha", country="Freedonia")
    assert qs.count() == 2


@pytest.mark.django_db
def test_location_str_method():
    """
    Test that __str__ returns the correct representation.
    """
    location = Location.objects.create(name="Display Site", code="DSP-01")
    assert str(location) == "Display Site (DSP-01)"


@pytest.mark.django_db
def test_location_update_and_timestamps():
    """
    Test that updating a location updates the updated_at timestamp.
    """
    location = Location.objects.create(name="Timestamped", code="TS-01")
    updated_at_before = location.updated_at
    location.name = "Timestamped Updated"
    location.save()
    location.refresh_from_db()
    assert location.updated_at > updated_at_before
    assert location.name == "Timestamped Updated"


@pytest.mark.django_db
def test_location_with_stocklevel_relationship():
    """
    Test relationship between Location and StockLevel (one-to-many).
    """
    location = Location.objects.create(name="Stock Room", code="STK-01")
    product1 = Product.objects.create(
        name="Widget X",
        sku="WX-1",
        description="Stocked widget",
        category="Widgets",
        price=Decimal("8.00"),
        current_stock=20,
    )
    product2 = Product.objects.create(
        name="Widget Y",
        sku="WY-2",
        description="Stocked widget",
        category="Widgets",
        price=Decimal("12.00"),
        current_stock=10,
    )
    stock1 = StockLevel.objects.create(product=product1, location=location, quantity=15)
    stock2 = StockLevel.objects.create(product=product2, location=location, quantity=8)
    # One location, two stock levels
    assert set(location.stocklevel_set.all()) == {stock1, stock2}
    # StockLevel __str__
    assert str(stock1) == "Widget X @ STK-01: 15"


@pytest.mark.django_db
def test_location_deletion_cascades_to_stocklevel():
    """
    Test that deleting a location cascades to StockLevel.
    """
    location = Location.objects.create(name="To Delete", code="DEL-01")
    product = Product.objects.create(
        name="Widget Z",
        sku="WZ-3",
        description="To be deleted",
        category="Widgets",
        price=Decimal("9.00"),
        current_stock=5,
    )
    StockLevel.objects.create(product=product, location=location, quantity=7)
    location.delete()
    assert StockLevel.objects.count() == 0
