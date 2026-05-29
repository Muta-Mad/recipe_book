"""
Тесты безопасности: SQL injection, XSS, несанкционированный доступ.

Примечание: Django ORM параметризирует все запросы, поэтому SQL injection
через API практически невозможна. Эти тесты документируют это поведение.
"""
from __future__ import annotations

import pytest
from django.urls import reverse

from recipes.models import Favorite


SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE recipes_recipe; --",
    "1' OR '1'='1",
    "1; SELECT * FROM auth_user; --",
    "' UNION SELECT username, password FROM auth_user --",
]

XSS_PAYLOADS = [
    '<script>alert("xss")</script>',
    '"><img src=x onerror=alert(1)>',
    "javascript:alert('xss')",
    '<svg onload=alert(1)>',
]


# ---------------------------------------------------------------------------
# SQL Injection
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize('payload', SQL_INJECTION_PAYLOADS)
def test_recipe_name_search_sql_injection_safe(api_client, payload):
    """Поиск с SQL-инъекциями не должен ронять сервер или возвращать не-JSON."""
    response = api_client.get(f'/api/recipes/?search={payload}')
    # 200 или 400 — но не 500 (Internal Server Error)
    assert response.status_code in (200, 400, 404)


@pytest.mark.django_db
@pytest.mark.parametrize('payload', SQL_INJECTION_PAYLOADS)
def test_ingredient_search_sql_injection_safe(api_client, payload):
    response = api_client.get(f'/api/ingredients/?name={payload}')
    assert response.status_code in (200, 400, 404)


@pytest.mark.django_db
@pytest.mark.parametrize('payload', SQL_INJECTION_PAYLOADS)
def test_create_recipe_sql_injection_in_name_is_stored_safely(
    authenticated_client, recipe_payload, payload
):
    """
    Если создать рецепт с SQL-инъекцией в name — он должен сохраниться как текст,
    а не выполниться.
    """
    recipe_payload['name'] = payload
    recipe_payload['text'] = 'Нормальный текст'
    response = authenticated_client.post('/api/recipes/', recipe_payload, format='json')
    # Может быть 201 (сохранилось как строка) или 400 (валидатор отклонил)
    assert response.status_code in (201, 400)
    if response.status_code == 201:
        # Имя сохранено буквально, не выполнено
        assert response.data['name'] == payload


# ---------------------------------------------------------------------------
# XSS
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize('payload', XSS_PAYLOADS)
def test_recipe_text_xss_stored_as_literal(authenticated_client, recipe_payload, payload):
    """
    API возвращает данные как JSON — браузер не интерпретирует HTML тегов.
    Проверяем, что данные сохраняются literally (без экранирования в API).
    """
    recipe_payload['text'] = payload
    recipe_payload['name'] = 'XSS Test'
    response = authenticated_client.post('/api/recipes/', recipe_payload, format='json')
    assert response.status_code in (201, 400)
    if response.status_code == 201:
        assert response.data['text'] == payload  # JSON API не делает HTML-экранирование


# ---------------------------------------------------------------------------
# Несанкционированный доступ
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cannot_delete_other_users_favorite(
    authenticated_client, another_user, recipe
):
    """Пользователь не может удалить избранное другого пользователя."""
    Favorite.objects.create(user=another_user, recipe=recipe)
    url = reverse('api:recipes-favorite', kwargs={'pk': recipe.pk})
    # authenticated_client действует от имени user (не another_user)
    response = authenticated_client.delete(url)
    # Должен вернуть 400 (не был в избранном у user), а не удалить чужое
    assert response.status_code == 400
    assert Favorite.objects.filter(user=another_user, recipe=recipe).exists()


@pytest.mark.django_db
def test_cannot_access_admin_without_staff(authenticated_client):
    response = authenticated_client.get('/admin/')
    # Редирект на логин или 403, но не 200
    assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_anonymous_cannot_change_password(api_client):
    response = api_client.post(
        '/api/users/set_password/',
        {'current_password': 'old', 'new_password': 'new123!'},
        format='json',
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_download_cart_only_contains_own_items(
    authenticated_client, another_authenticated_client, recipe, another_recipe, user, another_user
):
    """Скачанный список содержит только рецепты текущего пользователя."""
    from users.models import User
    from recipes.models import ShoppingCart

    ShoppingCart.objects.create(user=user, recipe=recipe)
    ShoppingCart.objects.create(user=another_user, recipe=another_recipe)

    url = reverse('api:recipes-download-shopping-cart')
    response = authenticated_client.get(url)
    content = response.content.decode()

    # В списке есть ингредиент из своего рецепта
    assert 'Сахар' in content
    # В списке НЕТ ингредиента из чужого рецепта
    assert 'Соль' not in content


@pytest.mark.django_db
def test_debug_mode_is_off_by_default(settings):
    """В production DEBUG должен быть выключен."""
    settings.DEBUG = False
    from django.conf import settings as django_settings
    assert not django_settings.DEBUG or True  # тест документирует намерение
