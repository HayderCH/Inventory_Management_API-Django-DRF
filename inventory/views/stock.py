from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from ..models import StockLevel, StockAdjustment, AuditLog, StockTransfer
from ..serializers import (
    StockLevelListSerializer,
    StockLevelDetailSerializer,
    StockLevelWriteSerializer,
    StockAdjustmentListSerializer,
    StockAdjustmentDetailSerializer,
    StockAdjustmentWriteSerializer,
    StockTransferDetailSerializer,
    StockTransferListSerializer,
    StockTransferWriteSerializer,
)
from ..permissions import IsAdmin, IsAnyOf, IsManager, IsEmployee, IsAuditor


class StockLevelViewSet(viewsets.ModelViewSet):
    queryset = StockLevel.objects.select_related("product", "location").all()

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["product", "location", "quantity"]
    search_fields = ["product__name", "location__name", "location__code"]
    ordering_fields = ["quantity", "updated_at"]
    ordering = ["-updated_at"]

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ["create", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsAnyOf(IsAdmin, IsManager)]
        elif self.action in ["list", "retrieve"]:
            return [
                permissions.IsAuthenticated(),
                IsAnyOf(IsAdmin, IsManager, IsEmployee, IsAuditor),
            ]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return StockLevelListSerializer
        elif self.action == "retrieve":
            return StockLevelDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return StockLevelWriteSerializer
        return StockLevelDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("product", "location")

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action="create",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": StockLevelDetailSerializer(instance).data},
        )

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action="update",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": StockLevelDetailSerializer(instance).data},
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        data = StockLevelDetailSerializer(instance).data
        AuditLog.objects.create(
            user=self.request.user,
            action="delete",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": data},
        )
        instance.delete()


class StockAdjustmentViewSet(viewsets.ModelViewSet):

    queryset = StockAdjustment.objects.select_related(
        "product", "location", "stock_transfer", "adjusted_by"
    )

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "product",
        "location",
        "adjustment_type",
        "stock_transfer",
        "adjusted_by",
        "created_at",
    ]
    search_fields = [
        "product__name",
        "location__name",
        "adjustment_type",
        "reason",
        "adjusted_by__username",
    ]
    ordering_fields = [
        "created_at",
        "quantity",
        "adjustment_type",
    ]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ["create", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsAnyOf(IsAdmin, IsManager)]
        elif self.action in ["list", "retrieve"]:
            return [
                permissions.IsAuthenticated(),
                IsAnyOf(IsAdmin, IsManager, IsEmployee, IsAuditor),
            ]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return StockAdjustmentListSerializer
        elif self.action == "retrieve":
            return StockAdjustmentDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return StockAdjustmentWriteSerializer
        return StockAdjustmentDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("product", "location", "stock_transfer", "adjusted_by")

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action="create",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": StockAdjustmentDetailSerializer(instance).data},
        )

    @transaction.atomic
    def perform_update(self, serializer):
        raise NotImplementedError("Stock adjustment cannot be updated once created.")

    @transaction.atomic
    def perform_destroy(self, instance):
        raise NotImplementedError("Stock adjustments cannot be deleted.")


class StockTransferViewSet(viewsets.ModelViewSet):
    queryset = StockTransfer.objects.select_related(
        "product", "from_location", "to_location", "requested_by", "approved_by"
    )

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "product",
        "from_location",
        "to_location",
        "status",
        "requested_by",
        "approved_by",
        "created_at",
    ]
    search_fields = [
        "product__name",
        "from_location__name",
        "to_location__name",
        "reason",
        "requested_by__username",
        "approved_by__username",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "quantity",
        "status",
    ]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ["create", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsAnyOf(IsAdmin, IsManager)]
        elif self.action in ["list", "retrieve"]:
            return [
                permissions.IsAuthenticated(),
                IsAnyOf(IsAdmin, IsManager, IsEmployee, IsAuditor),
            ]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return StockTransferListSerializer
        elif self.action == "retrieve":
            return StockTransferDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return StockTransferWriteSerializer
        return StockTransferDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "product", "from_location", "to_location", "requested_by", "approved_by"
        )

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save(requested_by=self.request.user, status="pending")
        AuditLog.objects.create(
            user=self.request.user,
            action="create",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": StockTransferDetailSerializer(instance).data},
        )

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action="update",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": StockTransferDetailSerializer(instance).data},
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        data = StockTransferDetailSerializer(instance).data
        AuditLog.objects.create(
            user=self.request.user,
            action="delete",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": data},
        )
        instance.delete()
