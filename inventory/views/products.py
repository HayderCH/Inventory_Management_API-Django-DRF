from rest_framework import viewsets, permissions, filters
from ..models import Product, ProductSupplier, AuditLog
from ..serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
    ProductSupplierListSerializer,
    ProductSupplierDetailSerializer,
    ProductSupplierWriteSerializer,
)
from ..permissions import IsAdmin, IsManager, IsEmployee, IsAuditor
from django_filters.rest_framework import DjangoFilterBackend


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ["create", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsAdmin() | IsManager()]
        elif self.action in ["list", "retrieve"]:
            return [
                permissions.IsAuthenticated(),
                IsAdmin() | IsManager() | IsEmployee() | IsAuditor(),
            ]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        elif self.action == "retrieve":
            return ProductDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProductWriteSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            return qs.prefetch_related("suppliers")
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
        data = ProductDetailSerializer(instance).data
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
    filterset_fields = ["category", "suppliers", "price"]
    search_fields = ["name", "sku", "description"]
    ordering_fields = ["name", "price", "created_at"]
    ordering = ["name"]


class ProductSupplierViewSet(viewsets.ModelViewSet):
    """
    Enterprise-grade ViewSet for the ProductSupplier (through) model.
    - Full audit logging on all mutations
    - Action-based permissions for fine-grained control
    - Optimized queries with select_related
    - Filtering, searching, and ordering for key business fields
    - Ready for extension (bulk ops, custom actions, etc.)
    """

    queryset = ProductSupplier.objects.select_related("product", "supplier").all()

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "product",
        "supplier",
        "is_preferred",
        "contract_start",
        "contract_end",
    ]
    search_fields = ["supplier_sku", "product__name", "supplier__name"]
    ordering_fields = [
        "supplier_price",
        "lead_time_days",
        "contract_start",
        "contract_end",
        "is_preferred",
    ]
    ordering = ["-is_preferred", "supplier_price"]

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ["create", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsAdmin() | IsManager()]
        elif self.action in ["list", "retrieve"]:
            return [
                permissions.IsAuthenticated(),
                IsAdmin() | IsManager() | IsEmployee() | IsAuditor(),
            ]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductSupplierListSerializer
        elif self.action == "retrieve":
            return ProductSupplierDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProductSupplierWriteSerializer
        return ProductSupplierDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("product", "supplier")

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
        data = ProductSupplierDetailSerializer(instance).data
        AuditLog.objects.create(
            user=self.request.user,
            action="delete",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": data},
        )
        instance.delete()
