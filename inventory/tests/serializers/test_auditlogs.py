import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from inventory.models import AuditLog
from inventory.serializers import AuditLogListSerializer, AuditLogDetailSerializer

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="audituser", password="testpass")


@pytest.fixture
def auditlog_instance(user):
    return AuditLog.objects.create(
        user=user,
        action="create",
        object_type="Product",
        object_id=123,
        timestamp=timezone.now(),
        extra={"field": "value"},
    )


@pytest.mark.django_db
def test_auditlog_list_serializer_output(auditlog_instance, user):
    serializer = AuditLogListSerializer(auditlog_instance)
    data = serializer.data
    assert data["id"] == auditlog_instance.id
    # User is nested serializer
    assert isinstance(data["user"], dict)
    assert data["user"]["id"] == user.id
    assert data["user"]["username"] == user.username
    assert data["action"] == "create"
    assert data["object_type"] == "Product"
    assert data["object_id"] == 123
    # ISO format for timestamp
    assert data["timestamp"] == auditlog_instance.timestamp.isoformat().replace(
        "+00:00", "Z"
    )
    assert data["extra"] == {"field": "value"}


@pytest.mark.django_db
def test_auditlog_detail_serializer_output(auditlog_instance, user):
    serializer = AuditLogDetailSerializer(auditlog_instance)
    data = serializer.data
    assert data["id"] == auditlog_instance.id
    assert isinstance(data["user"], dict)
    assert data["user"]["id"] == user.id
    assert data["user"]["username"] == user.username
    assert data["action"] == "create"
    assert data["object_type"] == "Product"
    assert data["object_id"] == 123
    assert data["timestamp"] == auditlog_instance.timestamp.isoformat().replace(
        "+00:00", "Z"
    )
    assert data["extra"] == {"field": "value"}


@pytest.mark.django_db
def test_auditlog_serializer_null_user():
    log = AuditLog.objects.create(
        user=None,
        action="update",
        object_type="StockTransfer",
        object_id=9,
        extra=None,
    )
    ser = AuditLogListSerializer(log)
    data = ser.data
    assert data["user"] is None


@pytest.mark.django_db
def test_auditlog_serializer_handles_empty_extra(user):
    log = AuditLog.objects.create(
        user=user,
        action="update",
        object_type="StockLevel",
        object_id=1,
        extra=None,
    )
    ser = AuditLogListSerializer(log)
    data = ser.data
    assert data["extra"] is None


@pytest.mark.django_db
def test_auditlog_serializer_read_only_fields(user):
    log = AuditLog.objects.create(
        user=user,
        action="delete",
        object_type="Location",
        object_id=77,
        extra={"note": "something"},
    )
    input_data = {
        "action": "create",
        "object_type": "Product",
        "object_id": 1,
        "extra": {"should_not_change": True},
    }
    serializer = AuditLogListSerializer(log, data=input_data)
    # DRF ignores all input for read-only fields; is_valid() is True, but validated_data is empty
    assert serializer.is_valid()
    assert serializer.validated_data == {}

    # Save should not alter the instance
    obj = serializer.save()
    log.refresh_from_db()
    assert log.action == "delete"
    assert log.object_type == "Location"
    assert log.object_id == 77
    assert log.extra == {"note": "something"}


@pytest.mark.django_db
def test_auditlog_serializer_invalid_action(user):
    log = AuditLog.objects.create(
        user=user,
        action="create",
        object_type="Product",
        object_id=1,
    )
    data = {
        "action": "invalid_action",
        "object_type": "Product",
        "object_id": 2,
    }
    serializer = AuditLogListSerializer(instance=log, data=data)
    # is_valid is True, validated_data is empty, and instance remains unchanged
    assert serializer.is_valid()
    assert serializer.validated_data == {}
    saved = serializer.save()
    log.refresh_from_db()
    assert log.action == "create"
    assert log.object_id == 1
