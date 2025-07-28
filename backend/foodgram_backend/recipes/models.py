from django.db import models

from users.models import CustomUser


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='recipe/images/')
    description = models.TextField()
    ingredients = models.ManyToManyField('Ingredient', through='RecipeIngredient')
    tags = models.ManyToManyField('Tag', related_name='recipes')
    text = models.TextField(default="описание",)
    cooking_time = models.IntegerField()
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)


class Tag(models.Model):
    """Модель Тегов."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=75, unique=True)


class Ingredient(models.Model):
    """Модель Ингридиентов."""

    name = models.CharField(max_length=50)
    measurement_unit = models.CharField(max_length=25)


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи Recipe-Ingredient."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    amount = models.IntegerField()


class Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name='favor_user',
        on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        related_name='favor_recipe',
        on_delete=models.CASCADE)


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name='shpg_user',
        on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        related_name='shpg_recipe',
        on_delete=models.CASCADE)
