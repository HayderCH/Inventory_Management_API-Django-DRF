from rest_framework import viewsets, mixins, filters

from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    DateTimeFromToRangeFilter,
    CharFilter,
    NumberFilter,
)
from ..models import AuditLog
from ..serializers import AuditLogListSerializer, AuditLogDetailSerializer
from ..permissions import IsAuditLogViewer


class AuditLogFilter(FilterSet):
    user = NumberFilter(field_name="user")
    action = CharFilter(field_name="action")
    object_type = CharFilter(field_name="object_type")
    object_id = NumberFilter(field_name="object_id")
    timestamp = DateTimeFromToRangeFilter(field_name="timestamp")

    class Meta:
        model = AuditLog
        fields = ["user", "action", "object_type", "object_id", "timestamp"]


class AuditLogViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = AuditLog.objects.select_related("user").all().order_by("-timestamp")
    serializer_class = AuditLogListSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AuditLogFilter
    ordering_fields = ["timestamp", "action", "object_type", "user"]
    search_fields = ["object_type", "action", "extra"]
    permission_classes = [IsAuditLogViewer]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AuditLogDetailSerializer
        return AuditLogListSerializer
