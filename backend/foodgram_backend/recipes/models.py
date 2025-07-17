from django.db import models

from users.models import CustomUser


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipe',
    )
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='recipe/imgage/')
    description = models.TextField()
    ingredients = models.ManyToManyField('Ingredient', through='RecipeIngredient')
    tags = models.ManyToManyField('Tag')
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

