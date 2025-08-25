from django.contrib.auth.models import AbstractUser
from django.db import models

from api.constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                           MAX_LENGTH_LAST_NAME)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""

    avatar = models.ImageField(upload_to='users/image/', blank=True, null=True)
    first_name = models.CharField(max_length=MAX_LENGTH_FIRST_NAME)
    last_name = models.CharField(max_length=MAX_LENGTH_LAST_NAME)
    email = models.EmailField(unique=True, max_length=MAX_LENGTH_EMAIL)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'


class Subscribe(models.Model):
    """Модель для подписок."""
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='subscribing',
    )
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='subscribers',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                name='%(app_label)s_%(class)s_unique_subscription',
                fields=['user', 'author'],
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_prevent_self_subscription',
                check=~models.Q(user=models.F('author'))
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} подписан на {self.author}'
