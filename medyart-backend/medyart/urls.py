from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from gallery.views import (
    PhotoViewSet,
    CommentViewSet,
    InteractionViewSet,
    RegisterView
)

router = DefaultRouter()
router.register(r'photos', PhotoViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'interactions', InteractionViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
