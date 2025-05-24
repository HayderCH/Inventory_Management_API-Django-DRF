from rest_framework import serializers
from ..models import AuditLog
from .short_serializers import UserShortSerializer


class AuditLogListSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action",
            "object_type",
            "object_id",
            "timestamp",
            "extra",
        ]
        read_only_fields = fields


class AuditLogDetailSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action",
            "object_type",
            "object_id",
            "timestamp",
            "extra",
        ]
        read_only_fields = fields
