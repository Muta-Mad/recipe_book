# import random

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import CustomUser


class Recipe(models.Model):
    """Модель рецепта с основными данными и связями."""

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='recipe/images/')
    ingredients = models.ManyToManyField(
        'Ingredient', through='RecipeIngredient'
    )
    tags = models.ManyToManyField('Tag', related_name='recipes')
    text = models.TextField(default='')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(32000)
        ]
    )
    # short_code = models.CharField(max_length=9, unique=True, blank=True)

    def __str__(self):
        return self.name

    # def generate_short_code(self):
    #     code = ''.join(random.choices('0123456789', k=6))
    #     return code

    # def save(self, *args, **kwargs):
    #     if not self.short_code:
    #         self.short_code = self.generate_short_code()
    #     super().save(*args, **kwargs)


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=75, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель Ингредиента."""

    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=25)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связующая модель рецепта и ингредиента."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(32000)
        ]
    )


class Favorite(models.Model):
    """Модель для хранения избранных рецептов."""
    user = models.ForeignKey(
        CustomUser,
        related_name='favor_user',
        on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        related_name='favor_recipe',
        on_delete=models.CASCADE, verbose_name='Рецептs')


class ShoppingCart(models.Model):
    """Модель корзины покупок."""
    user = models.ForeignKey(
        CustomUser,
        related_name='shpg_user',
        on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        related_name='shpg_recipe',
        on_delete=models.CASCADE)
