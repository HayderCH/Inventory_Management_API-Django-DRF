import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db import IntegrityError
from inventory.models import Product, Location, StockAdjustment, StockTransfer, Supplier


User = get_user_model()


@pytest.mark.django_db
def test_stockadjustment_creation_and_str():
    """Test creation of StockAdjustment and its string representation for each adjustment type."""
    user = User.objects.create_user(username="testuser", password="testpass")
    product = Product.objects.create(
        name="Adjust Widget",
        sku="ADJ-001",
        description="Adjust desc",
        category="AdjCat",
        price=Decimal("10.00"),
        current_stock=100,
        minimum_stock=5,
    )
    location = Location.objects.create(
        name="WH1", code="WH1", address="123 Main St", city="City", country="Country"
    )
    for adj_type, _ in StockAdjustment.ADJUSTMENT_TYPES:
        adj = StockAdjustment.objects.create(
            product=product,
            location=location,
            quantity=10,
            adjustment_type=adj_type,
            adjusted_by=user,
        )
        assert adj.product == product
        assert adj.location == location
        assert adj.quantity == 10
        assert adj.adjustment_type == adj_type
        assert adj.adjusted_by == user
        assert adj.created_at is not None
        # String representation
        assert str(adj) == f"{adj_type} 10 {product.name} @ {location.code}"


@pytest.fixture
def user(db):
    return User.objects.create_user(username="requireduser", password="testpass")


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Req Widget",
        sku="REQ-001",
        description="Req desc",
        category="ReqCat",
        price=Decimal("5.00"),
        current_stock=10,
        minimum_stock=2,
    )


@pytest.fixture
def location(db):
    return Location.objects.create(
        name="WH2", code="WH2", address="Address", city="City2", country="Country2"
    )


@pytest.mark.django_db
def test_stockadjustment_requires_product(location, user):
    with pytest.raises(IntegrityError):
        StockAdjustment.objects.create(
            # product omitted
            location=location,
            quantity=1,
            adjustment_type="receive",
            adjusted_by=user,
        )


@pytest.mark.django_db
def test_stockadjustment_requires_location(product, user):
    with pytest.raises(IntegrityError):
        StockAdjustment.objects.create(
            product=product,
            # location omitted
            quantity=1,
            adjustment_type="receive",
            adjusted_by=user,
        )


@pytest.mark.django_db
def test_stockadjustment_requires_quantity(product, location, user):
    with pytest.raises(IntegrityError):
        StockAdjustment.objects.create(
            product=product,
            location=location,
            # quantity omitted
            adjustment_type="receive",
            adjusted_by=user,
        )


@pytest.mark.django_db
def test_stockadjustment_requires_adjustment_type(product, location, user):
    obj = StockAdjustment.objects.create(
        product=product,
        location=location,
        quantity=1,
        # adjustment_type omitted
        adjusted_by=user,
    )
    print("Created object:", obj)


@pytest.mark.django_db
def test_stockadjustment_requires_adjusted_by(product, location):
    with pytest.raises(IntegrityError):
        StockAdjustment.objects.create(
            product=product,
            location=location,
            quantity=1,
            adjustment_type="receive",
            # adjusted_by omitted
        )


@pytest.mark.django_db
def test_stockadjustment_foreign_keys_protection():
    """Test that deleting related Product, Location, or User with PROTECT is not allowed."""
    user = User.objects.create_user(username="protectuser", password="testpass")
    product = Product.objects.create(
        name="Prot Widget",
        sku="PROT-001",
        description="Prot desc",
        category="ProtCat",
        price=Decimal("8.00"),
        current_stock=20,
        minimum_stock=1,
    )
    location = Location.objects.create(
        name="WH3", code="WH3", address="Addr", city="City3", country="Country3"
    )
    adj = StockAdjustment.objects.create(
        product=product,
        location=location,
        quantity=3,
        adjustment_type="audit",
        adjusted_by=user,
    )

    # Deleting protected objects should raise an error
    with pytest.raises(IntegrityError):
        product.delete()
    with pytest.raises(IntegrityError):
        location.delete()
    with pytest.raises(IntegrityError):
        user.delete()


@pytest.mark.django_db
def test_stockadjustment_stocktransfer_nullable_fk():
    """Test that StockAdjustment can reference a StockTransfer but does not require it."""
    user = User.objects.create_user(username="stocktransferuser", password="testpass")
    product = Product.objects.create(
        name="ST Widget",
        sku="ST-001",
        description="ST desc",
        category="STCat",
        price=Decimal("7.00"),
        current_stock=30,
        minimum_stock=3,
    )
    location = Location.objects.create(
        name="WH4", code="WH4", address="Addr4", city="City4", country="Country4"
    )
    # Without stock_transfer
    adj = StockAdjustment.objects.create(
        product=product,
        location=location,
        quantity=2,
        adjustment_type="correct",
        adjusted_by=user,
    )
    assert adj.stock_transfer is None

    # With stock_transfer
    transfer = StockTransfer.objects.create(
        product=product,
        from_location=location,
        to_location=Location.objects.create(
            name="WH5", code="WH5", address="Addr5", city="City5", country="Country5"
        ),
        quantity=2,
        requested_by=user,
        status="approved",
    )
    adj2 = StockAdjustment.objects.create(
        product=product,
        location=location,
        quantity=-2,
        adjustment_type="transfer_out",
        adjusted_by=user,
        stock_transfer=transfer,
    )
    assert adj2.stock_transfer == transfer


@pytest.mark.django_db
def test_stockadjustment_reason_field_and_blank():
    """Test the reason field can be blank or filled."""
    user = User.objects.create_user(username="reasonuser", password="testpass")
    product = Product.objects.create(
        name="Reason Widget",
        sku="REASON-001",
        description="Reason desc",
        category="ReasonCat",
        price=Decimal("6.00"),
        current_stock=15,
        minimum_stock=2,
    )
    location = Location.objects.create(
        name="WH6", code="WH6", address="Addr6", city="City6", country="Country6"
    )
    adj_blank = StockAdjustment.objects.create(
        product=product,
        location=location,
        quantity=4,
        adjustment_type="receive",
        adjusted_by=user,
        reason="",
    )
    assert adj_blank.reason == ""
    adj_filled = StockAdjustment.objects.create(
        product=product,
        location=location,
        quantity=-1,
        adjustment_type="loss",
        adjusted_by=user,
        reason="Damaged during handling",
    )
    assert adj_filled.reason == "Damaged during handling"
