"""
Общие фикстуры для всего тестового набора.
Запускать: pytest backend/tests/ из корня репозитория
"""
from __future__ import annotations

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

# Минимальный 1×1 GIF (35 байт) в виде base64 data-URL
TEST_IMAGE_B64 = (
    'data:image/gif;base64,'
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)


# ---------------------------------------------------------------------------
# API clients
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(user) -> APIClient:
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def another_authenticated_client(another_user) -> APIClient:
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=another_user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def admin_client_auth(admin_user) -> APIClient:
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123!',
        first_name='Иван',
        last_name='Тестов',
    )


@pytest.fixture
def another_user(db) -> User:
    return User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='testpass123!',
        first_name='Пётр',
        last_name='Другов',
    )


@pytest.fixture
def admin_user(db) -> User:
    return User.objects.create_superuser(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123!',
        first_name='Админ',
        last_name='Суперов',
    )


# ---------------------------------------------------------------------------
# Recipes catalog
# ---------------------------------------------------------------------------

@pytest.fixture
def tag(db) -> Tag:
    return Tag.objects.create(name='Завтрак', slug='breakfast')


@pytest.fixture
def tag2(db) -> Tag:
    return Tag.objects.create(name='Обед', slug='lunch')


@pytest.fixture
def ingredient(db) -> Ingredient:
    return Ingredient.objects.create(name='Сахар', measurement_unit='г')


@pytest.fixture
def ingredient2(db) -> Ingredient:
    return Ingredient.objects.create(name='Соль', measurement_unit='г')


@pytest.fixture
def recipe(db, user, tag, ingredient) -> Recipe:
    r = Recipe.objects.create(
        author=user,
        name='Тестовый рецепт',
        text='Описание тестового рецепта',
        cooking_time=30,
        image='recipe/images/test.gif',
    )
    r.tags.set([tag])
    RecipeIngredient.objects.create(recipe=r, ingredient=ingredient, amount=100)
    return r


@pytest.fixture
def another_recipe(db, another_user, tag2, ingredient2) -> Recipe:
    r = Recipe.objects.create(
        author=another_user,
        name='Чужой рецепт',
        text='Описание чужого рецепта',
        cooking_time=15,
        image='recipe/images/test2.gif',
    )
    r.tags.set([tag2])
    RecipeIngredient.objects.create(recipe=r, ingredient=ingredient2, amount=200)
    return r


@pytest.fixture
def recipe_payload(tag, ingredient) -> dict:
    """Корректные данные для создания рецепта (POST/PATCH)."""
    return {
        'name': 'Новый рецепт',
        'text': 'Описание нового рецепта',
        'cooking_time': 25,
        'image': TEST_IMAGE_B64,
        'tags': [tag.id],
        'ingredients': [{'id': ingredient.id, 'amount': 50}],
    }
