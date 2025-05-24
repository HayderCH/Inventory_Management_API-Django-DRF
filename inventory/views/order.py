from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from ..models import Order, OrderProduct, AuditLog
from ..serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderWriteSerializer,
    OrderProductListSerializer,
    OrderProductDetailSerializer,
    OrderProductWriteSerializer,
)
from ..permissions import IsAdmin, IsManager, IsEmployee, IsAuditor


class OrderViewSet(viewsets.ModelViewSet):
    """
    Enterprise-grade Order ViewSet with optimized querysets, permissions, audit logging, and transaction safety.
    """

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "supplier"]
    search_fields = ["order_number"]
    ordering_fields = ["created_at", "updated_at", "order_number", "status"]
    ordering = ["-created_at"]

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
            return OrderListSerializer
        elif self.action == "retrieve":
            return OrderDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return OrderWriteSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        qs = Order.objects.all()
        if self.action in ("list", "retrieve"):
            return qs.select_related("supplier").prefetch_related(
                "order_products__product"
            )
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            AuditLog.objects.create(
                user=self.request.user,
                action="create",
                object_type=instance.__class__.__name__,
                object_id=instance.pk,
                extra={"data": OrderDetailSerializer(instance).data},
            )

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            AuditLog.objects.create(
                user=self.request.user,
                action="update",
                object_type=instance.__class__.__name__,
                object_id=instance.pk,
                extra={"data": OrderDetailSerializer(instance).data},
            )

    def perform_destroy(self, instance):
        with transaction.atomic():
            data = OrderDetailSerializer(instance).data
            AuditLog.objects.create(
                user=self.request.user,
                action="delete",
                object_type=instance.__class__.__name__,
                object_id=instance.pk,
                extra={"data": data},
            )
            instance.delete()


class OrderProductViewSet(viewsets.ModelViewSet):
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["order", "product"]
    search_fields = ["product__name", "order__order_number"]
    ordering_fields = ["unit_price", "quantity"]
    ordering = ["-id"]

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
            return OrderProductListSerializer
        elif self.action == "retrieve":
            return OrderProductDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return OrderProductWriteSerializer
        return OrderProductDetailSerializer

    def get_queryset(self):
        qs = OrderProduct.objects.all()
        if self.action in ("list", "retrieve"):
            return qs.select_related("order", "product").prefetch_related(
                "product__suppliers"
            )
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            AuditLog.objects.create(
                user=self.request.user,
                action="create",
                object_type=instance.__class__.__name__,
                object_id=instance.pk,
                extra={"data": OrderProductDetailSerializer(instance).data},
            )

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            AuditLog.objects.create(
                user=self.request.user,
                action="update",
                object_type=instance.__class__.__name__,
                object_id=instance.pk,
                extra={"data": OrderProductDetailSerializer(instance).data},
            )

    def perform_destroy(self, instance):
        with transaction.atomic():
            data = OrderProductDetailSerializer(instance).data
            AuditLog.objects.create(
                user=self.request.user,
                action="delete",
                object_type=instance.__class__.__name__,
                object_id=instance.pk,
                extra={"data": data},
            )
            instance.delete()
