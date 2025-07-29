from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name="Электронная почта",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+\Z",
                message=(
                    "Логин может содержать только буквы, цифры и "
                    "@/./+/-/_"
                ),
            )
        ],
        verbose_name="Логин",
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия",
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        'User',
        related_name="subscriptions",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        'User',
        related_name="authors",
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_subscription"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="no_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"


class Product(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name="Название",
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name="Единица измерения",
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_product'
            )
        ]
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="recipes"
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название",
    )
    image = models.ImageField(
        upload_to="recipes/images/",
        verbose_name="Изображение",
    )
    text = models.TextField(
        verbose_name="Описание",
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Время приготовления (мин)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-created_at",)

    def __str__(self):
        return self.name


class ProductInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="products"
    )
    ingredient = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
        related_name="in_recipes"
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Продукты в рецепте"
        verbose_name_plural = "Продукты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_ingredient_in_recipe",
            )
        ]

    def __str__(self):
        return f"{self.ingredient} в {self.recipe}"


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="%(app_label)s_%(class)s_unique"
            )
        ]

    def __str__(self):
        return f"{self.user} взаимодействует с {self.recipe}"


class Favorite(UserRecipeRelation):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="favorites"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="favorites"
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"


class ShoppingCart(UserRecipeRelation):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="shopping_carts"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="shopping_carts"
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
