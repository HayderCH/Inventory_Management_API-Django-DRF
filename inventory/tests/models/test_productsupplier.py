import pytest
from inventory.models import Product, Supplier, ProductSupplier
import datetime
from decimal import Decimal


@pytest.mark.django_db
def test_productsupplier_creation_and_fields():
    """Test creation of ProductSupplier and all its fields."""
    product = Product.objects.create(
        name="Widget",
        sku="W-1",
        description="A widget",
        category="Tools",
        price=Decimal("10.99"),
        current_stock=20,
        minimum_stock=2,
    )
    supplier = Supplier.objects.create(
        name="ToolsCo",
        contact_name="Alice",
        contact_email="alice@toolsco.com",
        address="1 Tool St",
        city="Tooltown",
        country="Toolland",
        rating=5,
        contract_start=datetime.date.today(),
    )
    today = datetime.date.today()
    link = ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="T-W-1",
        supplier_price=Decimal("9.99"),
        lead_time_days=10,
        contract_start=today,
        contract_end=today + datetime.timedelta(days=365),
        is_preferred=True,
    )
    assert link.product == product
    assert link.supplier == supplier
    assert link.supplier_sku == "T-W-1"
    assert link.supplier_price == Decimal("9.99")
    assert link.lead_time_days == 10
    assert link.contract_start == today
    assert link.contract_end == today + datetime.timedelta(days=365)
    assert link.is_preferred is True
    assert str(link) == f"{product} from {supplier}"


@pytest.mark.django_db
def test_productsupplier_defaults():
    """Test default values for ProductSupplier fields."""
    product = Product.objects.create(
        name="Default Widget",
        sku="DW-1",
        description="Defaults",
        category="Tools",
        price=Decimal("5.00"),
        current_stock=10,
        minimum_stock=1,
    )
    supplier = Supplier.objects.create(
        name="DefaultCo",
        contact_name="Bob",
        contact_email="bob@defaultco.com",
        address="2 Default St",
        city="Default City",
        country="Defaultland",
        rating=7,
        contract_start=datetime.date.today(),
    )
    link = ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="D-DW-1",
        supplier_price=Decimal("4.50"),
    )
    assert link.lead_time_days == 0
    assert link.contract_start is None
    assert link.contract_end is None
    assert link.is_preferred is False


@pytest.mark.django_db
def test_productsupplier_unique_together_constraint():
    """Test unique constraint for product and supplier pair."""
    product = Product.objects.create(
        name="Uniq Widget",
        sku="UW-1",
        description="Unique",
        category="Tools",
        price=Decimal("20.00"),
        current_stock=5,
        minimum_stock=1,
    )
    supplier = Supplier.objects.create(
        name="UniqCo",
        contact_name="Eve",
        contact_email="eve@uniqco.com",
        address="3 Uniq St",
        city="Uniq City",
        country="Uniqland",
        rating=8,
        contract_start=datetime.date.today(),
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="U-UW-1",
        supplier_price=Decimal("18.00"),
    )
    with pytest.raises(Exception):
        ProductSupplier.objects.create(
            product=product,
            supplier=supplier,
            supplier_sku="U-UW-2",
            supplier_price=Decimal("17.00"),
        )


@pytest.mark.django_db
def test_productsupplier_deletion_cascade():
    """Test that deleting product or supplier cascades to ProductSupplier."""
    product = Product.objects.create(
        name="Cascade Widget",
        sku="CW-1",
        description="Cascade",
        category="Tools",
        price=Decimal("5.00"),
        current_stock=10,
        minimum_stock=1,
    )
    supplier = Supplier.objects.create(
        name="CascadeCo",
        contact_name="Carl",
        contact_email="carl@cascadeco.com",
        address="4 Cascade St",
        city="Cascade City",
        country="Cascadonia",
        rating=6,
        contract_start=datetime.date.today(),
    )
    link = ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="C-CW-1",
        supplier_price=Decimal("4.00"),
    )
    product.delete()
    assert ProductSupplier.objects.count() == 0


@pytest.mark.django_db
def test_productsupplier_supplier_delete():
    """Test that deleting supplier cascades to ProductSupplier."""
    product = Product.objects.create(
        name="Cascade Supplier Widget",
        sku="CSW-1",
        description="Cascade Supplier",
        category="Tools",
        price=Decimal("15.00"),
        current_stock=20,
        minimum_stock=2,
    )
    supplier = Supplier.objects.create(
        name="CascadeSupplierCo",
        contact_name="Daisy",
        contact_email="daisy@cascadesupplierco.com",
        address="5 Daisy St",
        city="Daisy City",
        country="Daisyland",
        rating=9,
        contract_start=datetime.date.today(),
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="CS-CSW-1",
        supplier_price=Decimal("14.00"),
    )
    supplier.delete()
    assert ProductSupplier.objects.count() == 0


@pytest.mark.django_db
def test_productsupplier_manager_relations():
    """Test the related managers for M2M through ProductSupplier."""
    supplier1 = Supplier.objects.create(
        name="Rel1",
        contact_name="R1",
        contact_email="r1@rel.co",
        address="R1 St",
        city="Relcity",
        country="Repub",
        rating=1,
        contract_start=datetime.date.today(),
    )
    supplier2 = Supplier.objects.create(
        name="Rel2",
        contact_name="R2",
        contact_email="r2@rel.co",
        address="R2 St",
        city="Relcity",
        country="Repub",
        rating=2,
        contract_start=datetime.date.today(),
    )
    product = Product.objects.create(
        name="RelWidget",
        sku="REL-1",
        description="Relational",
        category="Tools",
        price=Decimal("10.00"),
        current_stock=10,
        minimum_stock=1,
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier1,
        supplier_sku="PS-REL-1",
        supplier_price=Decimal("9.50"),
    )
    ProductSupplier.objects.create(
        product=product,
        supplier=supplier2,
        supplier_sku="PS-REL-2",
        supplier_price=Decimal("9.00"),
    )
    assert set(product.suppliers.all()) == {supplier1, supplier2}
    assert set(supplier1.products.all()) == {product}
    assert set(supplier2.products.all()) == {product}


@pytest.mark.django_db
def test_productsupplier_edge_cases():
    """Test edge cases for blank and null values."""
    product = Product.objects.create(
        name="Edge Widget",
        sku="EDGE-1",
        description="Edge",
        category="Tools",
        price=Decimal("1.00"),
        current_stock=1,
        minimum_stock=0,
    )
    supplier = Supplier.objects.create(
        name="EdgeCo",
        contact_name="Ed",
        contact_email="ed@edge.co",
        address="Edge St",
        city="Edge City",
        country="Edgeland",
        rating=0,
        contract_start=datetime.date.today(),
    )
    link = ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku="E-EDGE-1",
        supplier_price=Decimal("0.99"),
        # contract_start and contract_end omitted
    )
    assert link.contract_start is None
    assert link.contract_end is None
    assert link.is_preferred is False
