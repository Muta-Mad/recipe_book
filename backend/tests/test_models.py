"""Тесты моделей: валидация, ограничения, методы."""
from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
from users.models import Subscribe, User


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_recipe_str_contains_name_and_author(recipe):
    assert recipe.name in str(recipe)
    assert recipe.author.username in str(recipe)


@pytest.mark.django_db
def test_recipe_short_code_generated_on_save(recipe):
    assert recipe.short_code
    assert len(recipe.short_code) == 6
    assert recipe.short_code.isdigit()


@pytest.mark.django_db
def test_recipe_short_code_is_unique(user, tag, ingredient):
    r1 = Recipe.objects.create(
        author=user, name='Рецепт 1', text='Текст', cooking_time=10,
        image='recipe/images/test.gif',
    )
    r2 = Recipe.objects.create(
        author=user, name='Рецепт 2', text='Текст', cooking_time=10,
        image='recipe/images/test.gif',
    )
    assert r1.short_code != r2.short_code


@pytest.mark.django_db
def test_recipe_short_code_not_overwritten_on_resave(recipe):
    original_code = recipe.short_code
    recipe.name = 'Изменённое название'
    recipe.save()
    recipe.refresh_from_db()
    assert recipe.short_code == original_code


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tag_str(tag):
    assert tag.name in str(tag)
    assert tag.slug in str(tag)


@pytest.mark.django_db
def test_tag_slug_unique(tag):
    with pytest.raises(IntegrityError):
        Tag.objects.create(name='Другое', slug=tag.slug)


# ---------------------------------------------------------------------------
# Ingredient
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_ingredient_str(ingredient):
    assert ingredient.name in str(ingredient)
    assert ingredient.measurement_unit in str(ingredient)


@pytest.mark.django_db
def test_ingredient_unique_constraint(ingredient):
    with pytest.raises(IntegrityError):
        Ingredient.objects.create(
            name=ingredient.name,
            measurement_unit=ingredient.measurement_unit,
        )


# ---------------------------------------------------------------------------
# Favorite — DB-уровень UniqueConstraint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_favorite_unique_constraint(user, recipe):
    Favorite.objects.create(user=user, recipe=recipe)
    with pytest.raises(IntegrityError):
        Favorite.objects.create(user=user, recipe=recipe)


@pytest.mark.django_db
def test_favorite_str(user, recipe):
    fav = Favorite.objects.create(user=user, recipe=recipe)
    assert user.username in str(fav)
    assert recipe.name in str(fav)


# ---------------------------------------------------------------------------
# ShoppingCart — DB-уровень UniqueConstraint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_shopping_cart_unique_constraint(user, recipe):
    ShoppingCart.objects.create(user=user, recipe=recipe)
    with pytest.raises(IntegrityError):
        ShoppingCart.objects.create(user=user, recipe=recipe)


# ---------------------------------------------------------------------------
# Subscribe
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_subscribe_prevents_self_subscription(user):
    with pytest.raises(IntegrityError):
        Subscribe.objects.create(user=user, author=user)


@pytest.mark.django_db
def test_subscribe_unique_constraint(user, another_user):
    Subscribe.objects.create(user=user, author=another_user)
    with pytest.raises(IntegrityError):
        Subscribe.objects.create(user=user, author=another_user)


@pytest.mark.django_db
def test_subscribe_str(user, another_user):
    sub = Subscribe.objects.create(user=user, author=another_user)
    result = str(sub)
    assert result  # просто убеждаемся что не падает


# ---------------------------------------------------------------------------
# RecipeIngredient
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_recipe_ingredient_str(recipe, ingredient):
    ri = RecipeIngredient.objects.get(recipe=recipe, ingredient=ingredient)
    assert ingredient.name in str(ri)
    assert recipe.name in str(ri)


@pytest.mark.django_db
def test_recipe_ingredient_unique_constraint(recipe, ingredient):
    with pytest.raises(IntegrityError):
        RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, amount=50)
