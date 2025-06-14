from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Supplier, AuditLog
from ..serializers import (
    SupplierListSerializer,
    SupplierDetailSerializer,
    SupplierWriteSerializer,
)
from ..permissions import IsAdmin, IsAnyOf, IsManager, IsEmployee, IsAuditor


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ["create", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsAnyOf(IsAdmin, IsManager)]
        elif self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated(), IsAnyOf(IsAdmin, IsManager, IsEmployee, IsAuditor)]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return SupplierListSerializer
        elif self.action == "retrieve":
            return SupplierDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return SupplierWriteSerializer
        return SupplierDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            return qs.prefetch_related("products")
        return qs

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action="create",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": serializer.data},
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action="update",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": serializer.data},
        )

    def perform_destroy(self, instance):
        data = SupplierDetailSerializer(instance).data
        AuditLog.objects.create(
            user=self.request.user,
            action="delete",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": data},
        )
        instance.delete()

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["country", "city", "rating", "contract_start", "contract_end"]
    search_fields = ["name", "contact_name", "contact_email", "city", "country"]
    ordering_fields = [
        "name",
        "city",
        "country",
        "rating",
        "contract_start",
        "contract_end",
        "updated_at",
    ]
    ordering = ["name"]
