from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from users.models import User as User

class Ingredient(models.Model):
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
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        related_name="recipes",
        on_delete=models.CASCADE,
        verbose_name="Автор",
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
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        related_name="ingredients",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_ingredient_in_recipe",
            )
        ]

    def __str__(self):
        return f"{self.ingredient} в {self.recipe}"


class Favorite(models.Model):

    user = models.ForeignKey(
        User,
        related_name="favorites",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="favorited_by",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user} добавил {self.recipe} в избранное"


class ShoppingCart(models.Model):

    user = models.ForeignKey(
        User,
        related_name="shopping_cart",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="in_shopping_cart",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user} добавил {self.recipe} в список покупок"


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    short_code = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="Короткий код",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Короткая ссылка"
        verbose_name_plural = "Короткие ссылки"

    def __str__(self):
        return f"Короткая ссылка для {self.recipe}"