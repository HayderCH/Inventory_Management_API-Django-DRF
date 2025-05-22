from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action

from ..models import Location, AuditLog
from ..serializers import (
    LocationListSerializer,
    LocationDetailSerializer,
    LocationWriteSerializer,
)
from ..permissions import IsAdmin, IsManager, IsEmployee, IsAuditor


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by("-updated_at")

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["city", "country"]
    search_fields = ["name", "code", "address", "city", "country", "notes"]
    ordering_fields = ["name", "city", "country", "updated_at", "created_at"]
    ordering = ["-updated_at"]

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
            return LocationListSerializer
        elif self.action == "retrieve":
            return LocationDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return LocationWriteSerializer
        return LocationDetailSerializer

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
        data = LocationDetailSerializer(instance).data
        AuditLog.objects.create(
            user=self.request.user,
            action="delete",
            object_type=instance.__class__.__name__,
            object_id=instance.pk,
            extra={"data": data},
        )
        instance.delete()

    @action(detail=False, methods=["get"], url_path="distinct-countries")
    def distinct_countries(self, request):
        countries = Location.objects.values_list("country", flat=True).distinct()
        return Response({"countries": sorted(set(countries))})
