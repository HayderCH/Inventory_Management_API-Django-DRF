from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/inventory/", include("inventory.urls")),
    path("api/users/", include("user_management.urls")),
]
