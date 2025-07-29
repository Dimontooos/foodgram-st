from django_filters import rest_framework as filters
from recipes.models import Recipe, Product, User


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(method='filter_author')
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_author(self, recipes, name, value):
        if not User.objects.filter(id=value).exists():
            return recipes.none()
        return recipes.filter(author__id=value)

    def filter_favorited(self, recipes, name, value):
        recipes = recipes.select_related(
            'author').prefetch_related('favorites')
        if not self.request or self.request.user.is_anonymous:
            return recipes
        if value:
            return recipes.filter(favorites__user=self.request.user)
        return recipes.exclude(favorites__user=self.request.user)

    def filter_shopping_cart(self, recipes, name, value):
        recipes = recipes.select_related('author').prefetch_related(
            'shopping_carts'
        )
        if not self.request or self.request.user.is_anonymous:
            return recipes
        if value:
            return recipes.filter(shopping_carts__user=self.request.user)
        return recipes.exclude(shopping_carts__user=self.request.user)


class ProductFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Product
        fields = ['name']
