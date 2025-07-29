from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.db.models import Count
from .models import User, Subscription, Product, Recipe, ProductInRecipe, Favorite, ShoppingCart


class CookingTimeFilter(SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        recipes = Recipe.objects.all()
        if not recipes.exists():
            return [('fast', 'Быстрые (0)'), ('medium', 'Средние (0)'), ('long', 'Долгие (0)')]
        times = recipes.values_list('cooking_time', flat=True)
        max_time = max(times, default=60)
        fast_threshold = max_time // 3
        medium_threshold = (max_time // 3) * 2
        fast_count = recipes.filter(cooking_time__lte=fast_threshold).count()
        medium_count = recipes.filter(
            cooking_time__gt=fast_threshold, cooking_time__lte=medium_threshold).count()
        long_count = recipes.filter(cooking_time__gt=medium_threshold).count()
        return [
            ('fast', f'Быстрые (<= {fast_threshold} мин, {fast_count})'),
            ('medium', f'Средние (<= {medium_threshold} мин, {medium_count})'),
            ('long', f'Долгие (> {medium_threshold} мин, {long_count})'),
        ]

    def queryset(self, request, recipes):
        if not self.value():
            return recipes
        times = recipes.values_list('cooking_time', flat=True)
        max_time = max(times, default=60) if times else 60
        fast_threshold = max_time // 3
        medium_threshold = (max_time // 3) * 2
        if self.value() == 'fast':
            return recipes.filter(cooking_time__lte=fast_threshold)
        elif self.value() == 'medium':
            return recipes.filter(cooking_time__gt=fast_threshold, cooking_time__lte=medium_threshold)
        return recipes.filter(cooking_time__gt=medium_threshold)


class HasRecipesFilter(SimpleListFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        users = User.objects.annotate(recipe_count=Count('recipes'))
        yes_count = users.filter(recipe_count__gt=0).count()
        no_count = users.filter(recipe_count=0).count()
        return (
            ('yes', f'Да ({yes_count})'),
            ('no', f'Нет ({no_count})'),
        )

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.annotate(recipe_count=Count('recipes')).filter(recipe_count__gt=0)
        if self.value() == 'no':
            return users.annotate(recipe_count=Count('recipes')).filter(recipe_count=0)
        return users


class HasSubscriptionsFilter(SimpleListFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        users = User.objects.annotate(sub_count=Count('subscriptions'))
        yes_count = users.filter(sub_count__gt=0).count()
        no_count = users.filter(sub_count=0).count()
        return (
            ('yes', f'Да ({yes_count})'),
            ('no', f'Нет ({no_count})'),
        )

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.annotate(sub_count=Count('subscriptions')).filter(sub_count__gt=0)
        if self.value() == 'no':
            return users.annotate(sub_count=Count('subscriptions')).filter(sub_count=0)
        return users


class HasSubscribersFilter(SimpleListFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        users = User.objects.annotate(auth_count=Count('authors'))
        yes_count = users.filter(auth_count__gt=0).count()
        no_count = users.filter(auth_count=0).count()
        return (
            ('yes', f'Да ({yes_count})'),
            ('no', f'Нет ({no_count})'),
        )

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.annotate(auth_count=Count('authors')).filter(auth_count__gt=0)
        if self.value() == 'no':
            return users.annotate(auth_count=Count('authors')).filter(auth_count=0)
        return users


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'full_name', 'email', 'get_avatar',
        'recipes_count', 'subscriptions_count', 'subscribers_count'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', HasRecipesFilter,
                   HasSubscriptionsFilter, HasSubscribersFilter)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'avatar')
        }),
        ('Разрешения', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'password1', 'password2', 'avatar'
            ),
        }),
    )
    ordering = ('email',)
    readonly_fields = ('subscribers_count',)

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}".strip()

    @admin.display(description='Аватар')
    @mark_safe
    def get_avatar(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="50" height="50" style="object-fit: cover;" />'
        return 'Нет аватара'

    @admin.display(description='Рецепты')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписки')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def subscribers_count(self, user):
        return user.authors.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = (
        'user__username', 'user__email',
        'author__username', 'author__email'
    )
    list_filter = ('user', 'author')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count', 'in_recipes')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    ordering = ('name',)

    @admin.display(description='Рецепты')
    def recipes_count(self, product):
        return product.productinrecipe_set.count()

    @admin.display(description='Есть в рецептах')
    def in_recipes(self, product):
        return product.productinrecipe_set.exists()
    in_recipes.boolean = True


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author',
        'favorites_count', 'get_products', 'get_image'
    )
    search_fields = (
        'name', 'author__username',
        'author__email', 'text'
    )
    list_filter = ('author', CookingTimeFilter)
    readonly_fields = ('favorites_count',)
    ordering = ('-created_at',)

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Продукты')
    @mark_safe
    def get_products(self, recipe):
        products = recipe.products.all()
        return '<br>'.join(
            f"{item.ingredient.name} ({item.amount} {item.ingredient.measurement_unit})"
            for item in products
        )

    @admin.display(description='Картинка')
    @mark_safe
    def get_image(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="100" height="100" style="object-fit: cover;" />'
        return 'Нет картинки'


@admin.register(ProductInRecipe)
class ProductInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'get_product_name', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')
    ordering = ('recipe',)

    @admin.display(description='Продукт')
    def get_product_name(self, product_in_recipe):
        return product_in_recipe.ingredient.name


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = (
        'user__username', 'user__email',
        'recipe__name'
    )
    list_filter = ('user', 'recipe')
    ordering = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = (
        'user__username', 'user__email',
        'recipe__name'
    )
    list_filter = ('user', 'recipe')
    ordering = ('user',)
