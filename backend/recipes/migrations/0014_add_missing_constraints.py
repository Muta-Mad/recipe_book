"""
Добавляет отсутствующие DB-уровневые UniqueConstraint для Favorite, ShoppingCart
и RecipeIngredient, а также исправляет related_name у RecipeIngredient.ingredient.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0013_auto_20250825_1508'),
    ]

    operations = [
        # Favorite — уникальность на уровне БД
        migrations.AddConstraint(
            model_name='favorite',
            constraint=models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            ),
        ),
        # ShoppingCart — уникальность на уровне БД
        migrations.AddConstraint(
            model_name='shoppingcart',
            constraint=models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart',
            ),
        ),
        # RecipeIngredient — уникальность пары рецепт+ингредиент
        migrations.AddConstraint(
            model_name='recipeingredient',
            constraint=models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            ),
        ),
        # Переименование related_name: ingredients → ingredient_usages
        migrations.AlterField(
            model_name='recipeingredient',
            name='ingredient',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='ingredient_usages',
                to='recipes.ingredient',
                verbose_name='Ингредиент',
            ),
        ),
    ]
