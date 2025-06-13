from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

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
                message="Username может содержать только буквы, цифры и @/./+/-/_",
            )
        ],
        verbose_name="Имя пользователя",
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

    def __str__(self):
        return self.username or self.email

class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        related_name="subscriptions",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        related_name="subscribers",
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscription"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="no_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"