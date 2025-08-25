import random

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from api.constants import MAX_LENGTH
from users.models import CustomUser


class Recipe(models.Model):
    """Модель рецепта с основными данными и связями."""

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipe/images/',
        verbose_name='Изображение'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name='Теги'
    )
    text = models.TextField(
        default='',
        verbose_name='Текст'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(32000)
        ],
        verbose_name='Время приготовления'
    )
    short_code = models.CharField(
        max_length=9,
        unique=True,
        blank=True,
        verbose_name='Короткий код'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-id',)

    def __str__(self):
        return f'Рецепт: {self.name} (автор: {self.author.username})'

    def generate_short_code(self):
        code = ''.join(random.choices('0123456789', k=6))
        return code

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        max_length=MAX_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return f'Тег: {self.name} ({self.slug})'


class Ingredient(models.Model):
    """Модель Ингредиента."""

    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'Ингредиент: {self.name} ({self.measurement_unit})'


class RecipeIngredient(models.Model):
    """Связующая модель рецепта и ингредиента."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(32000)
        ],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        ordering = ('recipe',)

    def __str__(self):
        return (
            f'Ингредиент в рецепте: {self.ingredient.name} - '
            f'{self.amount} {self.ingredient.measurement_unit} '
            f'(рецепт: {self.recipe.name})'
        )


class Favorite(models.Model):
    """Модель для хранения избранных рецептов."""
    user = models.ForeignKey(
        CustomUser,
        related_name='favor_user',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favor_recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('-id',)

    def __str__(self):
        return f'Избранное: {self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель корзины покупок."""
    user = models.ForeignKey(
        CustomUser,
        related_name='shpg_user',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shpg_recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        ordering = ('-id',)

    def __str__(self):
        return f'Корзина: {self.user.username} - {self.recipe.name}'
