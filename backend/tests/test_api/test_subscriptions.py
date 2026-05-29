"""Тесты подписок, аватара пользователя."""
from __future__ import annotations

import pytest
from django.urls import reverse

from users.models import Subscribe


def subscribe_url(user_id: int) -> str:
    return reverse('api:users-subscribe', kwargs={'id': user_id})


SUBSCRIPTIONS_URL = '/api/users/subscriptions/'
AVATAR_URL = '/api/users/me/avatar/'


# ---------------------------------------------------------------------------
# Подписки
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_subscribe_returns_201(authenticated_client, another_user):
    response = authenticated_client.post(subscribe_url(another_user.id))
    assert response.status_code == 201
    assert response.data['id'] == another_user.id


@pytest.mark.django_db
def test_subscribe_response_contains_required_fields(authenticated_client, another_user):
    response = authenticated_client.post(subscribe_url(another_user.id))
    for field in ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count'):
        assert field in response.data, f'Нет поля {field}'


@pytest.mark.django_db
def test_subscribe_to_self_returns_400(authenticated_client, user):
    response = authenticated_client.post(subscribe_url(user.id))
    assert response.status_code == 400


@pytest.mark.django_db
def test_subscribe_twice_returns_400(authenticated_client, another_user, user):
    Subscribe.objects.create(user=user, author=another_user)
    response = authenticated_client.post(subscribe_url(another_user.id))
    assert response.status_code == 400


@pytest.mark.django_db
def test_subscribe_to_nonexistent_user_returns_404(authenticated_client):
    response = authenticated_client.post(subscribe_url(99999))
    assert response.status_code == 404


@pytest.mark.django_db
def test_subscribe_anonymous_returns_401(api_client, another_user):
    response = api_client.post(subscribe_url(another_user.id))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Отписка
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_unsubscribe_returns_204(authenticated_client, another_user, user):
    Subscribe.objects.create(user=user, author=another_user)
    response = authenticated_client.delete(subscribe_url(another_user.id))
    assert response.status_code == 204
    assert not Subscribe.objects.filter(user=user, author=another_user).exists()


@pytest.mark.django_db
def test_unsubscribe_when_not_subscribed_returns_400(authenticated_client, another_user):
    response = authenticated_client.delete(subscribe_url(another_user.id))
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Список подписок
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_subscriptions_list_returns_200(authenticated_client, user, another_user):
    Subscribe.objects.create(user=user, author=another_user)
    response = authenticated_client.get(SUBSCRIPTIONS_URL)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_subscriptions_list_anonymous_returns_401(api_client):
    response = api_client.get(SUBSCRIPTIONS_URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_subscriptions_list_has_recipes(
    authenticated_client, user, another_user, another_recipe
):
    Subscribe.objects.create(user=user, author=another_user)
    response = authenticated_client.get(SUBSCRIPTIONS_URL)
    assert response.status_code == 200
    subscribed_author = response.data['results'][0]
    assert subscribed_author['recipes_count'] == 1
    assert len(subscribed_author['recipes']) == 1


@pytest.mark.django_db
def test_subscriptions_recipes_limit_param(
    authenticated_client, user, another_user, another_recipe, ingredient, tag
):
    from recipes.models import Recipe, RecipeIngredient
    extra = Recipe.objects.create(
        author=another_user, name='Ещё рецепт', text='...', cooking_time=5,
        image='recipe/images/t.gif',
    )
    extra.tags.set([tag])
    RecipeIngredient.objects.create(recipe=extra, ingredient=ingredient, amount=1)

    Subscribe.objects.create(user=user, author=another_user)
    response = authenticated_client.get(SUBSCRIPTIONS_URL + '?recipes_limit=1')
    assert response.status_code == 200
    author_data = response.data['results'][0]
    assert len(author_data['recipes']) == 1
    assert author_data['recipes_count'] == 2


# ---------------------------------------------------------------------------
# is_subscribed флаг
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_is_subscribed_true_for_subscribed_author(
    authenticated_client, user, another_user
):
    Subscribe.objects.create(user=user, author=another_user)
    url = reverse('api:users-detail', kwargs={'id': another_user.id})
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.data['is_subscribed'] is True


@pytest.mark.django_db
def test_is_subscribed_false_when_not_subscribed(authenticated_client, another_user):
    url = reverse('api:users-detail', kwargs={'id': another_user.id})
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.data['is_subscribed'] is False


# ---------------------------------------------------------------------------
# Аватар
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_update_avatar_returns_200(authenticated_client):
    from tests.conftest import TEST_IMAGE_B64
    response = authenticated_client.put(
        AVATAR_URL, {'avatar': TEST_IMAGE_B64}, format='json'
    )
    assert response.status_code == 200
    assert 'avatar' in response.data


@pytest.mark.django_db
def test_update_avatar_without_image_returns_400(authenticated_client):
    response = authenticated_client.put(AVATAR_URL, {}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_delete_avatar_returns_204(authenticated_client):
    response = authenticated_client.delete(AVATAR_URL)
    assert response.status_code == 204


@pytest.mark.django_db
def test_avatar_requires_auth(api_client):
    response = api_client.put(AVATAR_URL, {}, format='json')
    assert response.status_code == 401
