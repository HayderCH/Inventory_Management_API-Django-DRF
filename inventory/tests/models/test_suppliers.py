import pytest
from inventory.models import Supplier, Product, ProductSupplier
import datetime
from decimal import Decimal


@pytest.mark.django_db
def test_supplier_creation_and_fields():
    """
    Test creation of a Supplier and all its fields.
    """
    today = datetime.date.today()
    supplier = Supplier.objects.create(
        name="Enterprise Supplier",
        contact_name="John Doe",
        contact_email="john@enterprise.com",
        contact_phone="1234567890",
        address="123 Enterprise Rd",
        city="Enterprise City",
        country="Freedonia",
        rating=8,
        contract_start=today,
        contract_end=today + datetime.timedelta(days=365),
        notes="Preferred supplier for enterprise widgets.",
    )
    assert supplier.name == "Enterprise Supplier"
    assert supplier.contact_name == "John Doe"
    assert supplier.contact_email == "john@enterprise.com"
    assert supplier.contact_phone == "1234567890"
    assert supplier.address == "123 Enterprise Rd"
    assert supplier.city == "Enterprise City"
    assert supplier.country == "Freedonia"
    assert supplier.rating == 8
    assert supplier.contract_start == today
    assert supplier.contract_end == today + datetime.timedelta(days=365)
    assert supplier.notes == "Preferred supplier for enterprise widgets."
    assert supplier.created_at is not None
    assert supplier.updated_at is not None
    assert str(supplier) == "Enterprise Supplier"


@pytest.mark.django_db
def test_supplier_default_and_blank_fields():
    """
    Test default values and blank fields for Supplier.
    """
    today = datetime.date.today()
    supplier = Supplier.objects.create(
        name="Blank Supplier",
        contact_name="Jane Doe",
        contact_email="jane@blanks.com",
        address="1 Blank St",
        city="Blanktown",
        country="Blankland",
        rating=0,
        contract_start=today,
    )
    assert supplier.contact_phone == ""
    assert supplier.contract_end is None
    assert supplier.notes == ""


@pytest.mark.django_db
def test_supplier_unique_constraint_is_not_enforced():
    """
    Test that Supplier.name is not unique (should allow duplicates).
    """
    today = datetime.date.today()
    Supplier.objects.create(
        name="Not Unique",
        contact_name="A",
        contact_email="a@notunique.com",
        address="A Street",
        city="A City",
        country="A Country",
        rating=1,
        contract_start=today,
    )
    supplier2 = Supplier.objects.create(
        name="Not Unique",
        contact_name="B",
        contact_email="b@notunique.com",
        address="B Street",
        city="B City",
        country="B Country",
        rating=2,
        contract_start=today,
    )
    assert supplier2.name == "Not Unique"


@pytest.mark.django_db
def test_supplier_related_products_many_to_many():
    """
    Test the M2M relationship from Supplier to Product via ProductSupplier.
    """
    today = datetime.date.today()
    supplier = Supplier.objects.create(
        name="Productful Supplier",
        contact_name="Carol",
        contact_email="carol@supplier.com",
        address="1 Product Way",
        city="Supply City",
        country="Supplierland",
        rating=10,
        contract_start=today,
    )
    product1 = Product.objects.create(
        name="Widget Pro",
        sku="WP-001",
        description="A pro widget",
        category="Widgets",
        price=Decimal("50.00"),
        current_stock=100,
        minimum_stock=10,
    )
    product2 = Product.objects.create(
        name="Widget Lite",
        sku="WL-002",
        description="A lite widget",
        category="Widgets",
        price=Decimal("25.00"),
        current_stock=50,
        minimum_stock=5,
    )
    ps1 = ProductSupplier.objects.create(
        product=product1,
        supplier=supplier,
        supplier_sku="SUP-WP-001",
        supplier_price=Decimal("45.00"),
        lead_time_days=5,
        contract_start=today,
        is_preferred=True,
    )
    ps2 = ProductSupplier.objects.create(
        product=product2,
        supplier=supplier,
        supplier_sku="SUP-WL-002",
        supplier_price=Decimal("22.00"),
        lead_time_days=7,
        contract_start=today,
        is_preferred=False,
    )
    assert set(supplier.products.all()) == {product1, product2}
    assert ps1.supplier == supplier
    assert ps2.supplier == supplier
    assert ps1.is_preferred is True
    assert ps2.is_preferred is False


@pytest.mark.django_db
def test_supplier_can_have_no_products():
    """
    Test that a Supplier can exist with no related products.
    """
    supplier = Supplier.objects.create(
        name="Solo Supplier",
        contact_name="Solo",
        contact_email="solo@supplier.com",
        address="1 Solo Lane",
        city="Alone",
        country="Soloia",
        rating=0,
        contract_start=datetime.date.today(),
    )
    assert supplier.products.count() == 0


@pytest.mark.django_db
def test_supplier_products_manager_queryset():
    """
    Test that the products manager returns the correct queryset.
    """
    supplier = Supplier.objects.create(
        name="Query Supplier",
        contact_name="Query",
        contact_email="query@supplier.com",
        address="Query Lane",
        city="Queryville",
        country="Queryland",
        rating=5,
        contract_start=datetime.date.today(),
    )
    product = Product.objects.create(
        name="Query Product",
        sku="QP-001",
        description="Product for manager test",
        category="Test",
        price=Decimal("10.00"),
        current_stock=10,
        minimum_stock=1,
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="QP-001-SUP",
        supplier_price=Decimal("9.00"),
        lead_time_days=3,
        contract_start=datetime.date.today(),
    )
    products = supplier.products.all()
    assert products.count() == 1
    assert products.first() == product


@pytest.mark.django_db
def test_supplier_update_and_timestamp_fields():
    """
    Test that updating a supplier updates the updated_at timestamp.
    """
    supplier = Supplier.objects.create(
        name="Timestamp Supplier",
        contact_name="Timestamp",
        contact_email="ts@supplier.com",
        address="Time Lane",
        city="Timeville",
        country="Timeland",
        rating=3,
        contract_start=datetime.date.today(),
    )
    updated_at_before = supplier.updated_at
    supplier.name = "Timestamp Supplier Updated"
    supplier.save()
    supplier.refresh_from_db()
    assert supplier.updated_at > updated_at_before
    assert supplier.name == "Timestamp Supplier Updated"


@pytest.mark.django_db
def test_supplier_contract_dates_blank_and_null():
    """
    Test that contract_end can be blank and null, but contract_start cannot.
    """
    today = datetime.date.today()
    supplier = Supplier.objects.create(
        name="Contract Test",
        contact_name="Contractor",
        contact_email="contract@test.com",
        address="Contract Lane",
        city="Contractville",
        country="Contractland",
        rating=6,
        contract_start=today,
        # contract_end omitted
    )
    assert supplier.contract_end is None
    assert supplier.contract_start == today
