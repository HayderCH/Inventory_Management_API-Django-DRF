import pytest
from django.utils import timezone
from inventory.models import Location
from inventory.serializers import (
    LocationListSerializer,
    LocationDetailSerializer,
    LocationWriteSerializer,
)


@pytest.fixture
def location(db):
    return Location.objects.create(
        name="Warehouse X",
        code="WHX",
        address="1234 Test St",
        city="Metropolis",
        country="Freedonia",
        notes="Main distribution center.",
    )


@pytest.mark.django_db
def test_location_list_serializer_output(location):
    serializer = LocationListSerializer(location)
    data = serializer.data
    assert data["id"] == location.id
    assert data["name"] == "Warehouse X"
    assert data["code"] == "WHX"
    assert data["city"] == "Metropolis"
    assert data["country"] == "Freedonia"
    # Datetime fields are ISO format
    assert data["updated_at"] == location.updated_at.isoformat().replace("+00:00", "Z")


@pytest.mark.django_db
def test_location_detail_serializer_output(location):
    serializer = LocationDetailSerializer(location)
    data = serializer.data
    assert data["id"] == location.id
    assert data["name"] == "Warehouse X"
    assert data["code"] == "WHX"
    assert data["address"] == "1234 Test St"
    assert data["city"] == "Metropolis"
    assert data["country"] == "Freedonia"
    assert data["notes"] == "Main distribution center."
    assert data["created_at"] == location.created_at.isoformat().replace("+00:00", "Z")
    assert data["updated_at"] == location.updated_at.isoformat().replace("+00:00", "Z")


@pytest.mark.django_db
def test_location_list_serializer_read_only(location):
    # Should not allow updates with ListSerializer (all read-only)
    payload = {
        "name": "New Name",
        "code": "NEWC",
        "city": "OtherCity",
        "country": "OtherCountry",
        "updated_at": timezone.now().isoformat(),
    }
    serializer = LocationListSerializer(location, data=payload)
    assert serializer.is_valid()
    assert serializer.validated_data == {}
    obj = serializer.save()
    location.refresh_from_db()
    # No changes
    assert location.name == "Warehouse X"
    assert location.code == "WHX"


@pytest.mark.django_db
def test_location_detail_serializer_partial_update(location):
    payload = {"name": "Central Depot"}
    serializer = LocationDetailSerializer(location, data=payload, partial=True)
    assert serializer.is_valid()
    # Only fields not read-only can be updated
    assert "name" in serializer.fields
    # But Meta.read_only_fields excludes "name"
    updated = serializer.save()
    location.refresh_from_db()
    # Should update name
    assert location.name == "Central Depot"


@pytest.mark.django_db
def test_location_write_serializer_valid_create(db):
    payload = {
        "name": "Depot Y",
        "code": "d3p0ty",
        "address": "789 Commerce Blvd",
        "city": "Uptown",
        "country": "Freedonia",
        "notes": "",
    }
    serializer = LocationWriteSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    obj = serializer.save()
    assert obj.name == "Depot Y"
    assert obj.code == "D3P0TY"  # validate_code should upper-case


@pytest.mark.django_db
def test_location_write_serializer_invalid_code_non_alnum(db):
    payload = {
        "name": "Depot Z",
        "code": "INVALID-CODE!",
        "address": "000 Nowhere",
        "city": "Nowhere",
        "country": "Nowhereland",
        "notes": "",
    }
    serializer = LocationWriteSerializer(data=payload)
    assert not serializer.is_valid()
    assert "code" in serializer.errors
    assert "alphanumeric" in serializer.errors["code"][0].lower()


@pytest.mark.django_db
def test_location_write_serializer_duplicate_code(location):
    payload = {
        "name": "Other Depot",
        "code": "whx",  # Same as existing, different case
        "address": "Elsewhere",
        "city": "Elsewhere",
        "country": "Freedonia",
        "notes": "",
    }
    serializer = LocationWriteSerializer(data=payload)
    assert not serializer.is_valid()
    assert "code" in serializer.errors
    assert "already exists" in serializer.errors["code"][0]


@pytest.mark.django_db
def test_location_write_serializer_update_self_code(location):
    # Should allow updating own code to same value (case-insensitive)
    payload = {
        "name": "Warehouse X",
        "code": "whx",
        "address": "1234 Test St",
        "city": "Metropolis",
        "country": "Freedonia",
        "notes": "Main distribution center.",
    }
    serializer = LocationWriteSerializer(location, data=payload)
    assert serializer.is_valid(), serializer.errors
    obj = serializer.save()
    assert obj.code == "WHX"


@pytest.mark.django_db
def test_location_write_serializer_missing_fields(db):
    payload = {
        "name": "No Code"
        # Missing code, address, city, country, notes
    }
    serializer = LocationWriteSerializer(data=payload)
    assert not serializer.is_valid()
    # Only code is required by default
    assert "code" in serializer.errors
    # Optionally, check that the *other* fields are not required
    for field in ["address", "city", "country", "notes"]:
        assert field not in serializer.errors
