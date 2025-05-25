from django.urls import path, include
from rest_framework.routers import DefaultRouter

from inventory.views.audit_log import AuditLogViewSet
from inventory.views.location import LocationViewSet
from inventory.views.order import OrderProductViewSet, OrderViewSet
from inventory.views.product import ProductSupplierViewSet, ProductViewSet
from inventory.views.stock import (
    StockAdjustmentViewSet,
    StockLevelViewSet,
    StockTransferViewSet,
)
from inventory.views.suppliers import SupplierViewSet


router = DefaultRouter()
router.register(r"products", ProductViewSet)
router.register(r"suppliers", SupplierViewSet)
router.register(r"product-suppliers", ProductSupplierViewSet)
router.register(r"locations", LocationViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"order-products", OrderProductViewSet)
router.register(r"stock-levels", StockLevelViewSet)
router.register(r"stock-adjustments", StockAdjustmentViewSet)
router.register(r"stock-transfers", StockTransferViewSet)
router.register(r"audit-log", AuditLogViewSet)

urlpatterns = [path("", include(router.urls))]
