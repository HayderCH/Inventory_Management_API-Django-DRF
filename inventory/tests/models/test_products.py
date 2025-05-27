import pytest
from inventory.models import Product, Supplier, ProductSupplier
import datetime
from decimal import Decimal


@pytest.mark.django_db
def test_product_creation_and_fields():
    """
    Test that a Product is created with correct fields and defaults.
    """
    product = Product.objects.create(
        name="Enterprise Widget",
        sku="EW-1000",
        description="Top-tier enterprise widget.",
        category="Widgets",
        price=Decimal("199.99"),
        current_stock=500,
        minimum_stock=20,
    )
    assert product.name == "Enterprise Widget"
    assert product.sku == "EW-1000"
    assert product.description == "Top-tier enterprise widget."
    assert product.category == "Widgets"
    assert product.price == Decimal("199.99")
    assert product.current_stock == 500
    assert product.minimum_stock == 20
    assert product.created_at is not None
    assert product.updated_at is not None
    assert product.suppliers.count() == 0
    assert str(product) == "Enterprise Widget (EW-1000)"


@pytest.mark.django_db
def test_product_unique_sku_constraint():
    """
    Test that SKU is unique for products.
    """
    Product.objects.create(
        name="Product A",
        sku="SKU-UNIQUE-1",
        description="A",
        category="Cat",
        price=Decimal("10.00"),
        current_stock=10,
        minimum_stock=1,
    )
    with pytest.raises(Exception):
        Product.objects.create(
            name="Product B",
            sku="SKU-UNIQUE-1",  # Duplicate SKU
            description="B",
            category="Cat",
            price=Decimal("12.00"),
            current_stock=10,
            minimum_stock=1,
        )


@pytest.mark.django_db
def test_product_supplier_m2m_relationship():
    """
    Test adding suppliers to a product using the through model and verify relationship.
    """
    supplier = Supplier.objects.create(
        name="Acme Supplies",
        contact_name="Alice Manager",
        contact_email="alice@acme.com",
        contact_phone="123456789",
        address="1 Acme Street",
        city="Metropolis",
        country="Freedonia",
        rating=5,
        contract_start=datetime.date.today(),
    )
    product = Product.objects.create(
        name="Acme Gadget",
        sku="AG-2000",
        description="Gadget supplied by Acme.",
        category="Gadgets",
        price=Decimal("49.99"),
        current_stock=300,
        minimum_stock=10,
    )
    # Add supplier via through model with extra fields
    link = ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="ACME-AG-2000",
        supplier_price=Decimal("39.99"),
        lead_time_days=14,
        contract_start=datetime.date.today(),
        is_preferred=True,
    )
    assert supplier in product.suppliers.all()
    assert product in supplier.products.all()
    assert link.supplier_sku == "ACME-AG-2000"
    assert link.is_preferred is True
    assert str(link) == f"{product} from {supplier}"


@pytest.mark.django_db
def test_product_can_have_multiple_suppliers():
    """
    Test that a product can have more than one supplier.
    """
    supplier1 = Supplier.objects.create(
        name="Supplier One",
        contact_name="Contact One",
        contact_email="one@supply.com",
        contact_phone="111111111",
        address="One Lane",
        city="Alpha",
        country="CountryA",
        rating=10,
        contract_start=datetime.date.today(),
    )
    supplier2 = Supplier.objects.create(
        name="Supplier Two",
        contact_name="Contact Two",
        contact_email="two@supply.com",
        contact_phone="222222222",
        address="Two Lane",
        city="Beta",
        country="CountryB",
        rating=8,
        contract_start=datetime.date.today(),
    )
    product = Product.objects.create(
        name="MultiSource Widget",
        sku="MSW-3000",
        description="Widget with multiple sources.",
        category="Widgets",
        price=Decimal("79.99"),
        current_stock=50,
        minimum_stock=5,
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier1,
        supplier_sku="MSW-1",
        supplier_price=Decimal("70.00"),
        lead_time_days=10,
        contract_start=datetime.date.today(),
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier2,
        supplier_sku="MSW-2",
        supplier_price=Decimal("72.00"),
        lead_time_days=15,
        contract_start=datetime.date.today(),
    )
    assert product.suppliers.count() == 2
    assert set(product.suppliers.all()) == {supplier1, supplier2}


@pytest.mark.django_db
def test_product_supplier_unique_together_constraint():
    """
    Test that the combination of product and supplier is unique in ProductSupplier.
    """
    supplier = Supplier.objects.create(
        name="Unique Supplier",
        contact_name="Unique Contact",
        contact_email="unique@supply.com",
        contact_phone="333333333",
        address="Unique Lane",
        city="Gamma",
        country="CountryC",
        rating=7,
        contract_start=datetime.date.today(),
    )
    product = Product.objects.create(
        name="Unique Product",
        sku="UP-4000",
        description="Product to test unique constraint.",
        category="Unique",
        price=Decimal("99.99"),
        current_stock=20,
        minimum_stock=2,
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="UNIQUE-PS",
        supplier_price=Decimal("95.00"),
        lead_time_days=7,
        contract_start=datetime.date.today(),
    )
    with pytest.raises(Exception):
        # Duplicate pair
        ProductSupplier.objects.create(
            product=product,
            supplier=supplier,
            supplier_sku="UNIQUE-PS2",
            supplier_price=Decimal("93.00"),
            lead_time_days=5,
            contract_start=datetime.date.today(),
        )


@pytest.mark.django_db
def test_product_minimum_stock_default():
    """
    Test that minimum_stock defaults to 0 if not specified.
    """
    product = Product.objects.create(
        name="Default Stock Widget",
        sku="DSW-5000",
        description="No minimum specified.",
        category="Defaults",
        price=Decimal("29.99"),
        current_stock=5,
    )
    assert product.minimum_stock == 0


@pytest.mark.django_db
def test_product_suppliers_manager_returns_correct_queryset():
    """
    Test that the suppliers manager returns the correct queryset for a product.
    """
    supplier = Supplier.objects.create(
        name="Query Supplier",
        contact_name="QS Contact",
        contact_email="qs@supply.com",
        contact_phone="444444444",
        address="QS Lane",
        city="Delta",
        country="CountryD",
        rating=5,
        contract_start=datetime.date.today(),
    )
    product = Product.objects.create(
        name="Query Widget",
        sku="QW-6000",
        description="Widget for queryset test.",
        category="Query",
        price=Decimal("19.99"),
        current_stock=60,
        minimum_stock=4,
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="QW-SUP",
        supplier_price=Decimal("17.00"),
        lead_time_days=4,
        contract_start=datetime.date.today(),
    )
    suppliers = product.suppliers.all()
    assert suppliers.count() == 1
    assert suppliers.first() == supplier


@pytest.mark.django_db
def test_product_update_and_timestamp_fields():
    """
    Test that updating a product updates the updated_at timestamp.
    """
    product = Product.objects.create(
        name="Timestamp Widget",
        sku="TSW-7000",
        description="Widget for timestamp test.",
        category="Time",
        price=Decimal("59.99"),
        current_stock=90,
        minimum_stock=12,
    )
    updated_at_before = product.updated_at
    product.name = "Timestamp Widget Updated"
    product.save()
    product.refresh_from_db()
    assert product.updated_at > updated_at_before
    assert product.name == "Timestamp Widget Updated"
