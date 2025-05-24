from rest_framework import serializers
from ..models import Location


class LocationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "code",
            "city",
            "country",
            "updated_at",
        ]
        read_only_fields = fields


class LocationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "code",
            "address",
            "city",
            "country",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class LocationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "name",
            "code",
            "address",
            "city",
            "country",
            "notes",
        ]

    def validate_code(self, value):
        value = value.upper()
        if not value.isalnum():
            raise serializers.ValidationError("Code must be alphanumeric.")
        qs = Location.objects.filter(code=value)
        if self.instance:  # On update, exclude self
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A location with this code already exists."
            )
        return value
