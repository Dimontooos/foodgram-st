from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User, Subscription
from recipes.models import (
    Ingredient, Recipe, IngredientInRecipe, Favorite, ShoppingCart, ShortLink
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'email', 'id', 'username', 'first_name', 'last_name',
        'is_subscribed', 'avatar'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')
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
    readonly_fields = ('is_subscribed',)

    def is_subscribed(self, obj):
        """Количество подписчиков."""
        return obj.subscribers.count()
    is_subscribed.short_description = 'Подписчики'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = (
        'user__username', 'user__email',
        'author__username', 'author__email'
    )
    list_filter = ('user', 'author')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'cooking_time',
        'favorites_count', 'in_shopping_cart_count'
    )
    search_fields = (
        'name', 'author__username',
        'author__email', 'text'
    )
    list_filter = ('author', 'cooking_time')
    readonly_fields = ('favorites_count', 'in_shopping_cart_count')
    ordering = ('-created_at',)

    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = 'В избранном'

    def in_shopping_cart_count(self, obj):
        return obj.in_shopping_cart.count()
    in_shopping_cart_count.short_description = 'В корзине'


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')
    ordering = ('recipe',)


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


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'short_code', 'created_at')
    search_fields = ('recipe__name', 'short_code')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
