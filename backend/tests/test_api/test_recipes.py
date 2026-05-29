"""CRUD-тесты для рецептов: статус-коды и содержимое ответа."""
from __future__ import annotations

import pytest
from django.urls import reverse

from recipes.models import Favorite, ShoppingCart


RECIPES_LIST_URL = '/api/recipes/'


def recipe_detail_url(pk: int) -> str:
    return reverse('api:recipes-detail', kwargs={'pk': pk})


def recipe_favorite_url(pk: int) -> str:
    return reverse('api:recipes-favorite', kwargs={'pk': pk})


def recipe_cart_url(pk: int) -> str:
    return reverse('api:recipes-shopping-cart', kwargs={'pk': pk})


# ---------------------------------------------------------------------------
# Чтение (GET)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_recipes_list_returns_200_for_anonymous(api_client, recipe):
    response = api_client.get(RECIPES_LIST_URL)
    assert response.status_code == 200
    assert response.data['count'] >= 1


@pytest.mark.django_db
def test_recipe_list_response_has_required_fields(api_client, recipe):
    response = api_client.get(RECIPES_LIST_URL)
    item = response.data['results'][0]
    for field in ('id', 'name', 'author', 'tags', 'ingredients', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart', 'image', 'text'):
        assert field in item, f'Отсутствует поле {field}'


@pytest.mark.django_db
def test_recipe_detail_returns_200_for_anonymous(api_client, recipe):
    response = api_client.get(recipe_detail_url(recipe.pk))
    assert response.status_code == 200
    assert response.data['id'] == recipe.pk
    assert response.data['name'] == recipe.name


@pytest.mark.django_db
def test_recipe_detail_returns_404_for_nonexistent(api_client):
    response = api_client.get(recipe_detail_url(99999))
    assert response.status_code == 404


@pytest.mark.django_db
def test_anonymous_is_favorited_is_false(api_client, recipe):
    response = api_client.get(recipe_detail_url(recipe.pk))
    assert response.data['is_favorited'] is False
    assert response.data['is_in_shopping_cart'] is False


# ---------------------------------------------------------------------------
# Создание (POST)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_create_recipe_returns_201_for_authenticated(
    authenticated_client, recipe_payload
):
    response = authenticated_client.post(
        RECIPES_LIST_URL, recipe_payload, format='json'
    )
    assert response.status_code == 201
    assert response.data['name'] == recipe_payload['name']


@pytest.mark.django_db
def test_create_recipe_returns_401_for_anonymous(api_client, recipe_payload):
    response = api_client.post(RECIPES_LIST_URL, recipe_payload, format='json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_recipe_without_ingredients_returns_400(
    authenticated_client, recipe_payload
):
    recipe_payload['ingredients'] = []
    response = authenticated_client.post(
        RECIPES_LIST_URL, recipe_payload, format='json'
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_recipe_with_duplicate_ingredients_returns_400(
    authenticated_client, recipe_payload, ingredient
):
    recipe_payload['ingredients'] = [
        {'id': ingredient.id, 'amount': 10},
        {'id': ingredient.id, 'amount': 20},
    ]
    response = authenticated_client.post(
        RECIPES_LIST_URL, recipe_payload, format='json'
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_recipe_without_tags_returns_400(
    authenticated_client, recipe_payload
):
    recipe_payload['tags'] = []
    response = authenticated_client.post(
        RECIPES_LIST_URL, recipe_payload, format='json'
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_recipe_with_empty_name_returns_400(
    authenticated_client, recipe_payload
):
    recipe_payload['name'] = '   '
    response = authenticated_client.post(
        RECIPES_LIST_URL, recipe_payload, format='json'
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_recipe_sets_author_to_current_user(
    authenticated_client, recipe_payload, user
):
    response = authenticated_client.post(
        RECIPES_LIST_URL, recipe_payload, format='json'
    )
    assert response.status_code == 201
    assert response.data['author']['id'] == user.id


# ---------------------------------------------------------------------------
# Обновление (PATCH)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_patch_recipe_returns_200_for_author(
    authenticated_client, recipe, recipe_payload
):
    url = recipe_detail_url(recipe.pk)
    response = authenticated_client.patch(url, recipe_payload, format='json')
    assert response.status_code == 200
    assert response.data['name'] == recipe_payload['name']


@pytest.mark.django_db
def test_patch_recipe_returns_403_for_non_author(
    another_authenticated_client, recipe, recipe_payload
):
    url = recipe_detail_url(recipe.pk)
    response = another_authenticated_client.patch(url, recipe_payload, format='json')
    assert response.status_code == 403


@pytest.mark.django_db
def test_patch_recipe_returns_401_for_anonymous(api_client, recipe, recipe_payload):
    url = recipe_detail_url(recipe.pk)
    response = api_client.patch(url, recipe_payload, format='json')
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Удаление (DELETE)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_delete_recipe_returns_204_for_author(authenticated_client, recipe):
    url = recipe_detail_url(recipe.pk)
    response = authenticated_client.delete(url)
    assert response.status_code == 204


@pytest.mark.django_db
def test_delete_recipe_returns_403_for_non_author(
    another_authenticated_client, recipe
):
    url = recipe_detail_url(recipe.pk)
    response = another_authenticated_client.delete(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_delete_recipe_returns_401_for_anonymous(api_client, recipe):
    url = recipe_detail_url(recipe.pk)
    response = api_client.delete(url)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Избранное
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_add_to_favorite_returns_201(authenticated_client, recipe):
    response = authenticated_client.post(recipe_favorite_url(recipe.pk))
    assert response.status_code == 201
    assert response.data['id'] == recipe.pk


@pytest.mark.django_db
def test_add_to_favorite_twice_returns_400(authenticated_client, recipe):
    authenticated_client.post(recipe_favorite_url(recipe.pk))
    response = authenticated_client.post(recipe_favorite_url(recipe.pk))
    assert response.status_code == 400


@pytest.mark.django_db
def test_remove_from_favorite_returns_204(authenticated_client, recipe, user):
    Favorite.objects.create(user=user, recipe=recipe)
    response = authenticated_client.delete(recipe_favorite_url(recipe.pk))
    assert response.status_code == 204


@pytest.mark.django_db
def test_remove_from_favorite_not_in_list_returns_400(authenticated_client, recipe):
    response = authenticated_client.delete(recipe_favorite_url(recipe.pk))
    assert response.status_code == 400


@pytest.mark.django_db
def test_favorite_anonymous_returns_401(api_client, recipe):
    response = api_client.post(recipe_favorite_url(recipe.pk))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Корзина
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_add_to_cart_returns_201(authenticated_client, recipe):
    response = authenticated_client.post(recipe_cart_url(recipe.pk))
    assert response.status_code == 201


@pytest.mark.django_db
def test_add_to_cart_twice_returns_400(authenticated_client, recipe):
    authenticated_client.post(recipe_cart_url(recipe.pk))
    response = authenticated_client.post(recipe_cart_url(recipe.pk))
    assert response.status_code == 400


@pytest.mark.django_db
def test_remove_from_cart_returns_204(authenticated_client, recipe, user):
    ShoppingCart.objects.create(user=user, recipe=recipe)
    response = authenticated_client.delete(recipe_cart_url(recipe.pk))
    assert response.status_code == 204


@pytest.mark.django_db
def test_remove_from_cart_not_in_list_returns_400(authenticated_client, recipe):
    response = authenticated_client.delete(recipe_cart_url(recipe.pk))
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Скачать список покупок
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_download_shopping_cart_returns_200(authenticated_client, recipe, user):
    ShoppingCart.objects.create(user=user, recipe=recipe)
    url = reverse('api:recipes-download-shopping-cart')
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain'
    assert 'attachment' in response['Content-Disposition']


@pytest.mark.django_db
def test_download_shopping_cart_anonymous_returns_401(api_client):
    url = reverse('api:recipes-download-shopping-cart')
    response = api_client.get(url)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Short link
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_get_short_link_returns_200(api_client, recipe):
    url = reverse('api:recipes-get-link', kwargs={'pk': recipe.pk})
    response = api_client.get(url)
    assert response.status_code == 200
    assert 'short-link' in response.data


@pytest.mark.django_db
def test_short_link_redirect(client, recipe):
    response = client.get(f'/s/{recipe.short_code}/')
    assert response.status_code == 302
    assert f'/recipes/{recipe.pk}/' in response['Location']
