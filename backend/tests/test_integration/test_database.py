"""
Интеграционные тесты: проверка количества SQL-запросов (N+1 detection).

pytest.mark.integration — помечаем их как медленные интеграционные тесты.
"""
from __future__ import annotations

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from users.models import Subscribe, User


def _make_user(n: int) -> User:
    return User.objects.create_user(
        username=f'user{n}', email=f'user{n}@test.com', password='pass',
        first_name='A', last_name='B',
    )


@pytest.fixture
def bulk_recipes(db, user, tag, ingredient):
    """Создаёт 10 рецептов для тестирования N+1."""
    recipes = []
    for i in range(10):
        r = Recipe.objects.create(
            author=user,
            name=f'Рецепт {i}',
            text='Текст',
            cooking_time=10 + i,
            image='recipe/images/test.gif',
        )
        r.tags.set([tag])
        RecipeIngredient.objects.create(recipe=r, ingredient=ingredient, amount=i + 1)
        recipes.append(r)
    return recipes


@pytest.mark.integration
@pytest.mark.django_db
def test_recipe_list_query_count_is_bounded(bulk_recipes, user):
    """
    Список из 10 рецептов должен выполняться за O(1) запросов, а не O(N).
    Без select_related/prefetch_related — ~4+N запросов. После оптимизации — ≤ 8.
    """
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    with CaptureQueriesContext(connection) as ctx:
        response = client.get('/api/recipes/')

    assert response.status_code == 200
    num_queries = len(ctx.captured_queries)
    # Должно быть ≤ 8 запросов независимо от количества рецептов
    # (auth, paginator count, recipes+prefetch, favorites set, cart set)
    assert num_queries <= 8, (
        f'Слишком много SQL-запросов: {num_queries}. '
        f'Возможен N+1. Запросы:\n'
        + '\n'.join(q['sql'] for q in ctx.captured_queries)
    )


@pytest.mark.integration
@pytest.mark.django_db
def test_subscriptions_list_query_count_is_bounded(db, user, another_user, tag, ingredient):
    """
    Список подписок на 5 авторов с рецептами должен быть bounded.
    """
    authors = [_make_user(i + 100) for i in range(5)]
    for author in authors:
        Subscribe.objects.create(user=user, author=author)
        for j in range(3):
            r = Recipe.objects.create(
                author=author, name=f'Рецепт {author.id}-{j}',
                text='Текст', cooking_time=10,
                image='recipe/images/test.gif',
            )
            r.tags.set([tag])
            RecipeIngredient.objects.create(recipe=r, ingredient=ingredient, amount=1)

    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    with CaptureQueriesContext(connection) as ctx:
        response = client.get('/api/users/subscriptions/')

    assert response.status_code == 200
    num_queries = len(ctx.captured_queries)
    # Без prefetch — 1 + 5*3 = 16 запросов. После оптимизации — ≤ 8.
    assert num_queries <= 8, (
        f'N+1 в subscriptions: {num_queries} запросов. '
        + '\n'.join(q['sql'] for q in ctx.captured_queries)
    )


@pytest.mark.integration
@pytest.mark.django_db
def test_recipe_list_with_favorites_query_count(bulk_recipes, user):
    """is_favorited/is_in_shopping_cart должны использовать sets, а не N запросов."""
    for recipe in bulk_recipes[:5]:
        Favorite.objects.create(user=user, recipe=recipe)
        ShoppingCart.objects.create(user=user, recipe=recipe)

    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    with CaptureQueriesContext(connection) as ctx:
        response = client.get('/api/recipes/')

    assert response.status_code == 200
    num_queries = len(ctx.captured_queries)
    assert num_queries <= 10, (
        f'Слишком много запросов с избранным/корзиной: {num_queries}'
    )

    # Проверяем что is_favorited корректно работает
    results = response.data['results']
    favorited_ids = {recipe.pk for recipe in bulk_recipes[:5]}
    for item in results:
        if item['id'] in favorited_ids:
            assert item['is_favorited'] is True
            assert item['is_in_shopping_cart'] is True
        else:
            assert item['is_favorited'] is False
