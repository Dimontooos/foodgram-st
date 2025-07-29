from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, RecipeViewSet, UserViewSet

router = DefaultRouter()
router.register(
    r'ingredients',
    ProductViewSet,
    basename='ingredients'
)
router.register(
    r'recipes',
    RecipeViewSet,
    basename='recipes'
)
router.register(
    r'users',
    UserViewSet,
    basename='users'
)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
