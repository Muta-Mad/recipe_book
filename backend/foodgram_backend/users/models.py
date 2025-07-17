from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""

    avatar = models.ImageField(upload_to='users/image/', blank=True, null=True)

    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class Subscribe(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='subscribers',
    )

    class Meta:
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

