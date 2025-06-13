from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartDownloadView,
    UserViewSet
)


router = DefaultRouter()
router.register(
    r'ingredients',
    IngredientViewSet,
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


@ensure_csrf_cookie
def get_csrf_token(request):
    return HttpResponse(status=204)


urlpatterns = [
    path(
        'recipes/download_shopping_cart/',
        ShoppingCartDownloadView.as_view(),
        name='download_shopping_cart'
    ),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'users/subscriptions/',
        UserViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),
    path(
        'users/<int:pk>/subscribe/',
        UserViewSet.as_view(
            {'post': 'subscribe', 'delete': 'subscribe'}
        ),
        name='user-subscribe'
    ),
    path(
        'users/me/avatar/',
        UserViewSet.as_view(
            {'put': 'me_avatar', 'delete': 'me_avatar'}
        ),
        name='user-avatar'
    ),
    path(
        'users/set_password/',
        UserViewSet.as_view({'post': 'set_password'}),
        name='set-password'
    ),
    path('', include(router.urls)),
    path('get-csrf-token/', get_csrf_token, name='get_csrf_token'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
