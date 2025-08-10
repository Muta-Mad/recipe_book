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
    cooking_time = models.IntegerField()

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=75, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель Ингредиента."""

    name = models.CharField(max_length=50)
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
    amount = models.IntegerField()


class Favorite(models.Model):
    """Модель для хранения избранных рецептов."""
    user = models.ForeignKey(
        CustomUser,
        related_name='favor_user',
        on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        related_name='favor_recipe',
        on_delete=models.CASCADE, verbose_name='Избранное')


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
