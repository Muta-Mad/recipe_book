"""Тесты аутентификации: регистрация, логин, токен, текущий пользователь."""
from __future__ import annotations

import pytest
from django.urls import reverse

LOGIN_URL = '/api/auth/token/login/'
LOGOUT_URL = '/api/auth/token/logout/'
REGISTER_URL = '/api/users/'
ME_URL = '/api/users/me/'


# ---------------------------------------------------------------------------
# Регистрация
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_register_new_user_returns_201(api_client):
    data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpass123!',
        'first_name': 'Новый',
        'last_name': 'Пользователь',
    }
    response = api_client.post(REGISTER_URL, data, format='json')
    assert response.status_code == 201
    assert response.data['email'] == data['email']
    assert 'password' not in response.data


@pytest.mark.django_db
def test_register_duplicate_email_returns_400(api_client, user):
    data = {
        'username': 'other',
        'email': user.email,
        'password': 'pass123!',
        'first_name': 'А',
        'last_name': 'Б',
    }
    response = api_client.post(REGISTER_URL, data, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_missing_required_fields_returns_400(api_client):
    response = api_client.post(REGISTER_URL, {'email': 'x@x.com'}, format='json')
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Логин / получение токена
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_login_with_valid_credentials_returns_token(api_client, user):
    response = api_client.post(
        LOGIN_URL,
        {'email': user.email, 'password': 'testpass123!'},
        format='json',
    )
    assert response.status_code == 200
    assert 'auth_token' in response.data


@pytest.mark.django_db
def test_login_wrong_password_returns_400(api_client, user):
    response = api_client.post(
        LOGIN_URL,
        {'email': user.email, 'password': 'wrongpassword'},
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_nonexistent_user_returns_400(api_client):
    response = api_client.post(
        LOGIN_URL,
        {'email': 'ghost@example.com', 'password': 'nopass'},
        format='json',
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Текущий пользователь
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_me_returns_200_for_authenticated(authenticated_client, user):
    response = authenticated_client.get(ME_URL)
    assert response.status_code == 200
    assert response.data['email'] == user.email
    assert response.data['username'] == user.username


@pytest.mark.django_db
def test_me_returns_401_for_anonymous(api_client):
    response = api_client.get(ME_URL)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Список пользователей
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_users_list_accessible_anonymously(api_client, user):
    url = reverse('api:users-list')
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_detail_requires_auth(api_client, user):
    url = reverse('api:users-detail', kwargs={'id': user.id})
    response = api_client.get(url)
    assert response.status_code == 401
