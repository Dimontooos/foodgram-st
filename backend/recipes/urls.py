from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<str:short_code>/',
         RecipeViewSet.as_view({'get': 'short_link_redirect'}), name='short-link-redirect'),
]
