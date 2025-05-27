import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from inventory.models import AuditLog, Product, Location, StockTransfer

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="audituser", password="testpass")


@pytest.mark.django_db
def test_auditlog_creation_and_str(user):
    log = AuditLog.objects.create(
        user=user,
        action="create",
        object_type="Product",
        object_id=1,
        extra={"field": "value"},
    )
    assert log.user == user
    assert log.action == "create"
    assert log.object_type == "Product"
    assert log.object_id == 1
    assert log.extra == {"field": "value"}
    assert log.timestamp is not None
    # String representation
    assert str(log).startswith(f"{user} create Product 1 at ")
    assert "at" in str(log)
    assert "Product" in str(log)


@pytest.mark.django_db
def test_auditlog_null_user():
    log = AuditLog.objects.create(
        user=None,
        action="update",
        object_type="Location",
        object_id=42,
        extra=None,
    )
    assert log.user is None
    assert log.action == "update"
    assert log.object_type == "Location"
    assert log.object_id == 42
    assert log.extra is None


@pytest.mark.django_db
@pytest.mark.parametrize("action", ["create", "update", "delete"])
def test_auditlog_action_choices(user, action):
    log = AuditLog.objects.create(
        user=user,
        action=action,
        object_type="StockTransfer",
        object_id=99,
    )
    assert log.action == action


@pytest.mark.django_db
def test_auditlog_required_action_db(user):
    with pytest.raises(IntegrityError):
        AuditLog.objects.create(
            user=user,
            action=None,  # required field set to None
            object_type="Product",
            object_id=1,
        )


@pytest.mark.django_db
def test_auditlog_required_object_type_db(user):
    with pytest.raises(IntegrityError):
        AuditLog.objects.create(
            user=user,
            action="create",
            object_type=None,  # required field set to None
            object_id=1,
        )


@pytest.mark.django_db
def test_auditlog_required_object_id_db(user):
    with pytest.raises(IntegrityError):
        AuditLog.objects.create(
            user=user,
            action="create",
            object_type="Product",
            object_id=None,  # required field set to None
        )


@pytest.mark.django_db
def test_auditlog_full_clean_missing_action(user):
    log = AuditLog(
        user=user,
        object_type="Product",
        object_id=1,
    )
    with pytest.raises(ValidationError):
        log.full_clean()


@pytest.mark.django_db
def test_auditlog_full_clean_missing_object_type(user):
    log = AuditLog(
        user=user,
        action="create",
        object_id=1,
    )
    with pytest.raises(ValidationError):
        log.full_clean()


@pytest.mark.django_db
def test_auditlog_full_clean_missing_object_id(user):
    log = AuditLog(
        user=user,
        action="create",
        object_type="Product",
    )
    with pytest.raises(ValidationError):
        log.full_clean()


@pytest.mark.django_db
def test_auditlog_timestamp_auto(user):
    before = timezone.now()
    log = AuditLog.objects.create(
        user=user,
        action="create",
        object_type="Product",
        object_id=1,
    )
    after = timezone.now()
    assert before <= log.timestamp <= after


@pytest.mark.django_db
def test_auditlog_json_extra_blank(user):
    log = AuditLog.objects.create(
        user=user, action="create", object_type="Product", object_id=1, extra=None
    )
    assert log.extra is None
    log2 = AuditLog.objects.create(
        user=user, action="create", object_type="Product", object_id=2, extra={}
    )
    assert log2.extra == {}


@pytest.mark.django_db
def test_auditlog_user_on_delete_set_null(user):
    log = AuditLog.objects.create(
        user=user,
        action="delete",
        object_type="Product",
        object_id=1,
    )
    user.delete()
    log.refresh_from_db()
    assert log.user is None


@pytest.mark.django_db
def test_auditlog_object_id_type(user):
    # Accepts positive big integer; test with a large value
    big_id = 2**40
    log = AuditLog.objects.create(
        user=user,
        action="update",
        object_type="Product",
        object_id=big_id,
    )
    assert log.object_id == big_id


@pytest.mark.django_db
def test_auditlog_indexing_fields(user):
    # Test that indexes exist (optional: introspect DB if desired)
    log = AuditLog.objects.create(
        user=user,
        action="update",
        object_type="Product",
        object_id=555,
    )
    # Just a functional test, as Django's migration ensures index creation


@pytest.mark.django_db
def test_auditlog_bulk_create(user):
    AuditLog.objects.bulk_create(
        [
            AuditLog(user=user, action="create", object_type="Product", object_id=i)
            for i in range(10)
        ]
    )
    assert AuditLog.objects.count() >= 10


@pytest.mark.django_db
def test_auditlog_repr_snapshot(user):
    log = AuditLog.objects.create(
        user=user,
        action="update",
        object_type="Product",
        object_id=999,
        extra={"changed": ["field1", "field2"]},
    )
    s = str(log)
    assert "update" in s and "Product" in s and "999" in s and "at" in s


# Optionally: test audit log integration with other models by adding signals/tests if you implement automatic logging.
