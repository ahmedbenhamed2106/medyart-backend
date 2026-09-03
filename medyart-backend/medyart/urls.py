from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from gallery.views import PhotoViewSet

router = DefaultRouter()
router.register(r'photos', PhotoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
