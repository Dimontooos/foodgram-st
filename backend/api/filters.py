from django_filters import rest_framework as filters
from recipes.models import Recipe, Ingredient
from users.models import User

class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(method='filter_author')
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_author(self, queryset, name, value):
        if not User.objects.filter(id=value).exists():
            return queryset.none()
        return queryset.filter(author__id=value)

    def filter_favorited(self, queryset, name, value):
        queryset = queryset.select_related('author').prefetch_related('favorited_by')
        if not self.request or self.request.user.is_anonymous:
            return queryset  
        if value:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset.exclude(favorited_by__user=self.request.user)

    def filter_shopping_cart(self, queryset, name, value):
        queryset = queryset.select_related('author').prefetch_related('in_shopping_cart')
        if not self.request or self.request.user.is_anonymous:
            return queryset 
        if value:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        return queryset.exclude(in_shopping_cart__user=self.request.user)


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']