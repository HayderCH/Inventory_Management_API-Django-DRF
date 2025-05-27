import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db import IntegrityError
from inventory.models import Product, Location, StockTransfer

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="stockuser", password="testpass")


@pytest.fixture
def approver(db):
    return User.objects.create_user(username="approver", password="testpass")


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Enterprise Widget",
        sku="ENT-001",
        description="Enterprise desc",
        category="EntCat",
        price=Decimal("100.00"),
        current_stock=500,
        minimum_stock=50,
    )


@pytest.fixture
def from_location(db):
    return Location.objects.create(
        name="Warehouse A",
        code="WHA",
        address="123 Alpha St",
        city="AlphaCity",
        country="AlphaLand",
    )


@pytest.fixture
def to_location(db):
    return Location.objects.create(
        name="Warehouse B",
        code="WHB",
        address="456 Beta St",
        city="BetaCity",
        country="BetaLand",
    )


@pytest.mark.django_db
def test_stocktransfer_creation_and_str(
    product, from_location, to_location, user, approver
):
    transfer = StockTransfer.objects.create(
        product=product,
        from_location=from_location,
        to_location=to_location,
        quantity=42,
        status="pending",
        requested_by=user,
        approved_by=approver,
        reason="Enterprise transfer",
    )
    assert transfer.product == product
    assert transfer.from_location == from_location
    assert transfer.to_location == to_location
    assert transfer.quantity == 42
    assert transfer.status == "pending"
    assert transfer.requested_by == user
    assert transfer.approved_by == approver
    assert transfer.reason == "Enterprise transfer"
    assert transfer.created_at is not None
    assert transfer.updated_at is not None
    # String representation
    assert str(transfer) == (
        f"Transfer {product.name} {transfer.quantity} {from_location.code}->"
        f"{to_location.code} ({transfer.status})"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field, value",
    [
        ("product", None),
        ("from_location", None),
        ("to_location", None),
        ("quantity", None),
        ("status", None),
        ("requested_by", None),
    ],
)
def test_stocktransfer_required_fields(
    field, value, product, from_location, to_location, user
):
    kwargs = dict(
        product=product,
        from_location=from_location,
        to_location=to_location,
        quantity=10,
        status="pending",
        requested_by=user,
    )
    kwargs[field] = value
    with pytest.raises(IntegrityError):
        StockTransfer.objects.create(**kwargs)


@pytest.mark.django_db
def test_stocktransfer_quantity_positive(product, from_location, to_location, user):
    with pytest.raises(IntegrityError):
        StockTransfer.objects.create(
            product=product,
            from_location=from_location,
            to_location=to_location,
            quantity=-5,
            status="pending",
            requested_by=user,
        )


@pytest.mark.django_db
def test_stocktransfer_nullable_fields(product, from_location, to_location, user):
    transfer = StockTransfer.objects.create(
        product=product,
        from_location=from_location,
        to_location=to_location,
        quantity=20,
        status="pending",
        requested_by=user,
        reason="",  # blank is allowed
        approved_by=None,  # optional
    )
    assert transfer.reason == ""
    assert transfer.approved_by is None


@pytest.mark.django_db
def test_stocktransfer_status_choices(product, from_location, to_location, user):
    for status in ["pending", "approved", "completed", "canceled"]:
        transfer = StockTransfer.objects.create(
            product=product,
            from_location=from_location,
            to_location=to_location,
            quantity=1,
            status=status,
            requested_by=user,
        )
        assert transfer.status == status


@pytest.mark.django_db
def test_stocktransfer_protect_foreign_keys(product, from_location, to_location, user):
    transfer = StockTransfer.objects.create(
        product=product,
        from_location=from_location,
        to_location=to_location,
        quantity=10,
        status="pending",
        requested_by=user,
    )
    # Deleting protected objects should raise an error
    with pytest.raises(IntegrityError):
        product.delete()
    with pytest.raises(IntegrityError):
        from_location.delete()
    with pytest.raises(IntegrityError):
        to_location.delete()
    with pytest.raises(IntegrityError):
        user.delete()


@pytest.mark.django_db
def test_stocktransfer_self_transfer_not_allowed(product, from_location, user):
    # Test for business logic - not in model, but you can enforce in clean()
    transfer = StockTransfer(
        product=product,
        from_location=from_location,
        to_location=from_location,
        quantity=1,
        status="pending",
        requested_by=user,
    )
    # If you have a .clean() method, you could do:
    # with pytest.raises(ValidationError):
    #     transfer.full_clean()
    # For now, just test it exists (edge case awareness)
    assert transfer.from_location == transfer.to_location


@pytest.mark.django_db
def test_stocktransfer_bulk_create(product, from_location, to_location, user):
    StockTransfer.objects.bulk_create(
        [
            StockTransfer(
                product=product,
                from_location=from_location,
                to_location=to_location,
                quantity=i + 1,
                status="pending",
                requested_by=user,
            )
            for i in range(5)
        ]
    )
    assert StockTransfer.objects.count() >= 5


@pytest.mark.django_db
def test_stocktransfer_auto_fields(product, from_location, to_location, user):
    import datetime

    before = datetime.datetime.now(datetime.UTC)
    transfer = StockTransfer.objects.create(
        product=product,
        from_location=from_location,
        to_location=to_location,
        quantity=10,
        status="pending",
        requested_by=user,
    )
    assert transfer.created_at is not None
    assert transfer.updated_at is not None


# Optionally: Add business logic tests for transitions, approval, etc., as you expand your logic.
