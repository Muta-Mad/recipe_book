"""Тесты разрешений: аноним, авторизованный пользователь, автор, чужой."""
from __future__ import annotations

import pytest
from django.urls import reverse

# ---------------------------------------------------------------------------
# Анонимный пользователь
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anonymous_can_read_recipe_list(api_client, recipe):
    response = api_client.get('/api/recipes/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_anonymous_can_read_recipe_detail(api_client, recipe):
    url = reverse('api:recipes-detail', kwargs={'pk': recipe.pk})
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_anonymous_cannot_create_recipe(api_client, recipe_payload):
    response = api_client.post('/api/recipes/', recipe_payload, format='json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_cannot_delete_recipe(api_client, recipe):
    url = reverse('api:recipes-detail', kwargs={'pk': recipe.pk})
    response = api_client.delete(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_cannot_add_to_favorite(api_client, recipe):
    url = reverse('api:recipes-favorite', kwargs={'pk': recipe.pk})
    response = api_client.post(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_cannot_add_to_cart(api_client, recipe):
    url = reverse('api:recipes-shopping-cart', kwargs={'pk': recipe.pk})
    response = api_client.post(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_cannot_download_cart(api_client):
    url = reverse('api:recipes-download-shopping-cart')
    response = api_client.get(url)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Авторизованный пользователь (не автор рецепта)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_non_author_cannot_delete_other_users_recipe(
    another_authenticated_client, recipe
):
    url = reverse('api:recipes-detail', kwargs={'pk': recipe.pk})
    response = another_authenticated_client.delete(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_non_author_cannot_patch_other_users_recipe(
    another_authenticated_client, recipe, recipe_payload
):
    url = reverse('api:recipes-detail', kwargs={'pk': recipe.pk})
    response = another_authenticated_client.patch(url, recipe_payload, format='json')
    assert response.status_code == 403


@pytest.mark.django_db
def test_non_author_can_add_other_recipe_to_favorite(
    another_authenticated_client, recipe
):
    url = reverse('api:recipes-favorite', kwargs={'pk': recipe.pk})
    response = another_authenticated_client.post(url)
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# Автор рецепта
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_author_can_delete_own_recipe(authenticated_client, recipe):
    url = reverse('api:recipes-detail', kwargs={'pk': recipe.pk})
    response = authenticated_client.delete(url)
    assert response.status_code == 204


@pytest.mark.django_db
def test_author_can_patch_own_recipe(authenticated_client, recipe, recipe_payload):
    url = reverse('api:recipes-detail', kwargs={'pk': recipe.pk})
    response = authenticated_client.patch(url, recipe_payload, format='json')
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Теги и ингредиенты — публичные read-only
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tags_list_accessible_to_anonymous(api_client, tag):
    url = reverse('api:tags-list')
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_ingredients_list_accessible_to_anonymous(api_client, ingredient):
    url = reverse('api:ingredients-list')
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_tags_are_read_only_for_authenticated(authenticated_client, tag):
    url = reverse('api:tags-list')
    response = authenticated_client.post(url, {'name': 'X', 'slug': 'x'}, format='json')
    assert response.status_code == 405
