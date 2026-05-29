<div align="center">

# 🍽️ Foodgram — Recipe Book

**Платформа для публикации рецептов, подписок на авторов и составления списков покупок**

[![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-3.2-092E20?style=flat-square&logo=django&logoColor=white)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.12-red?style=flat-square)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

[**🌐 Открыть проект**](https://foodgram-yandex.ddns.net) · [**📖 API Docs**](https://foodgram-yandex.ddns.net/api/docs/) · [**🐛 Сообщить об ошибке**](https://github.com/Muta-Mad/foodgram/issues)

</div>

---

## 📋 О проекте

**Foodgram** — это полнофункциональное веб-приложение для любителей кулинарии. Пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное, подписываться на авторов и скачивать сводный список продуктов для выбранных блюд.

### ✨ Ключевые возможности

| Функция | Описание |
|---------|----------|
| 📝 **Рецепты** | Создание, редактирование и удаление рецептов с фото |
| 🔖 **Избранное** | Сохранение понравившихся рецептов |
| 🛒 **Список покупок** | Автоматическое суммирование ингредиентов из выбранных рецептов |
| 👥 **Подписки** | Подписка на авторов и просмотр их рецептов в ленте |
| 🏷️ **Теги** | Фильтрация рецептов по завтрак/обед/ужин |
| 🔗 **Короткие ссылки** | Уникальный короткий URL для каждого рецепта |
| 📥 **Экспорт** | Скачивание списка покупок в формате `.txt` |

---

## 🏗️ Архитектура

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│    Nginx    │────▶│   Django    │
│  Frontend   │     │  (reverse   │     │   Backend   │
│             │     │   proxy)    │     │    (DRF)    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │ PostgreSQL  │
                                        │     DB      │
                                        └─────────────┘
```

### Стек технологий

**Backend**
- [Django 3.2](https://djangoproject.com) + [Django REST Framework 3.12](https://www.django-rest-framework.org)
- [Djoser](https://djoser.readthedocs.io) — аутентификация (Token Auth)
- [django-filter](https://django-filter.readthedocs.io) — фильтрация рецептов
- [Gunicorn](https://gunicorn.org) — WSGI-сервер

**Frontend**
- [React](https://reactjs.org)

**Инфраструктура**
- [PostgreSQL 13](https://postgresql.org) — база данных
- [Nginx](https://nginx.org) — веб-сервер и reverse proxy
- [Docker](https://docker.com) + [Docker Compose](https://docs.docker.com/compose/)
- [GitHub Actions](https://github.com/features/actions) — CI/CD

---

## 🚀 Быстрый старт

### Требования

- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+

### 1. Клонирование репозитория

```bash
git clone https://github.com/Muta-Mad/foodgram.git
cd foodgram
```

### 2. Настройка окружения

Создайте файл `.env` в корне проекта на основе примера:

```bash
cp .env.example .env
```

Заполните `.env`:

```env
# Static files
STATIC_ROOT=/backend_static/static

# Django
SECRET_KEY=your-secret-key-50-chars-minimum
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# CORS (для production)
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# База данных
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your_strong_password
DB_HOST=db
DB_PORT=5432
```

### 3. Запуск

```bash
# Сборка и запуск всех контейнеров
cd infra
docker compose up -d --build

# Применение миграций
docker compose exec backend python manage.py migrate

# Сбор статики
docker compose exec backend python manage.py collectstatic --noinput

# Создание суперпользователя
docker compose exec backend python manage.py createsuperuser
```

### 4. Загрузка начальных данных (опционально)

```bash
# Загрузить список из ~2000 ингредиентов
docker compose exec backend python manage.py loaddata ingredients.json
```

### 5. Готово! 🎉

| Сервис | URL |
|--------|-----|
| 🌐 Приложение | http://localhost:8000 |
| ⚙️ Админ-панель | http://localhost:8000/admin/ |
| 📖 API | http://localhost:8000/api/ |

---

## 🔌 API

### Аутентификация

Проект использует **Token Authentication**. Токен передаётся в заголовке:
```
Authorization: Token <ваш_токен>
```

#### Получить токен

```http
POST /api/auth/token/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

```json
{
  "auth_token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Основные эндпоинты

#### Пользователи

```http
GET    /api/users/                  # Список пользователей
POST   /api/users/                  # Регистрация
GET    /api/users/me/               # Текущий пользователь
PUT    /api/users/me/avatar/        # Обновить аватар
DELETE /api/users/me/avatar/        # Удалить аватар
POST   /api/users/{id}/subscribe/   # Подписаться
DELETE /api/users/{id}/subscribe/   # Отписаться
GET    /api/users/subscriptions/    # Мои подписки
```

#### Рецепты

```http
GET    /api/recipes/                          # Список (с фильтрами)
POST   /api/recipes/                          # Создать рецепт
GET    /api/recipes/{id}/                     # Детали рецепта
PATCH  /api/recipes/{id}/                     # Обновить рецепт
DELETE /api/recipes/{id}/                     # Удалить рецепт
GET    /api/recipes/{id}/get-link/            # Короткая ссылка
POST   /api/recipes/{id}/favorite/            # В избранное
DELETE /api/recipes/{id}/favorite/            # Из избранного
POST   /api/recipes/{id}/shopping_cart/       # В корзину
DELETE /api/recipes/{id}/shopping_cart/       # Из корзины
GET    /api/recipes/download_shopping_cart/   # Скачать список покупок
```

#### Фильтры рецептов

| Параметр | Тип | Описание |
|----------|-----|----------|
| `tags` | slug | Фильтр по тегу (можно несколько) |
| `author` | int | Фильтр по ID автора |
| `is_favorited` | 0/1 | Только избранные |
| `is_in_shopping_cart` | 0/1 | Только в корзине |
| `limit` | int | Размер страницы |

```bash
# Примеры
GET /api/recipes/?tags=breakfast&tags=lunch
GET /api/recipes/?author=5&is_favorited=1
GET /api/recipes/?limit=3&page=2
```

#### Теги и ингредиенты

```http
GET /api/tags/                     # Все теги
GET /api/ingredients/              # Поиск ингредиентов
GET /api/ingredients/?name=соль    # Поиск по началу названия
```

---

## 🧪 Тесты

### Запуск тестов

```bash
# Из корня проекта
cd backend
pytest ../backend/tests/ -v

# С отчётом о покрытии
pytest ../backend/tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### Структура тестов

```
backend/tests/
├── conftest.py                        # Общие фикстуры
├── test_models.py                     # Тесты моделей и ограничений БД
├── test_security.py                   # SQL injection, XSS, доступ
├── test_api/
│   ├── test_auth.py                   # Регистрация, логин, токен
│   ├── test_recipes.py                # CRUD рецептов (29 тестов)
│   ├── test_permissions.py            # Права: анон / автор / чужой
│   └── test_subscriptions.py          # Подписки, аватар
└── test_integration/
    └── test_database.py               # Проверка N+1 (assertNumQueries)
```

### Покрытие

```bash
pytest backend/tests/ --cov=. --cov-report=term-missing --cov-fail-under=70
```

---

## ⚙️ Разработка

### Локальный запуск без Docker

```bash
cd backend

# Создать виртуальное окружение
python3.9 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Настроить окружение
cp ../.env.example .env
# Отредактировать .env: USE_SQLITE=True, DEBUG=True

# Применить миграции
python manage.py migrate

# Запустить сервер
python manage.py runserver
```

### Переменные окружения

| Переменная | Обязательная | По умолчанию | Описание |
|-----------|:---:|---------|----------|
| `SECRET_KEY` | ✅ | — | Секретный ключ Django |
| `DEBUG` | ❌ | `False` | Режим отладки |
| `ALLOWED_HOSTS` | ✅ | `localhost,127.0.0.1` | Разрешённые хосты |
| `STATIC_ROOT` | ❌ | `backend/collected_static` | Путь сборки статики; в Docker — `/backend_static/static` |
| `CORS_ALLOWED_ORIGINS` | ❌ | — | Разрешённые CORS origins (через запятую) |
| `POSTGRES_DB` | ✅ | `django` | Имя БД |
| `POSTGRES_USER` | ✅ | `django` | Пользователь БД |
| `POSTGRES_PASSWORD` | ✅ | — | Пароль БД |
| `DB_HOST` | ✅ | — | Хост БД |
| `DB_PORT` | ❌ | `5432` | Порт БД |
| `USE_SQLITE` | ❌ | `False` | Использовать SQLite вместо PostgreSQL |

---

## 🚢 CI/CD

При каждом push в ветку `main` автоматически:

```
push → main
    │
    ├─ 🧪 tests          pytest + flake8
    │        │
    │        ▼ (только при успехе)
    ├─ 🐳 build backend  → DockerHub
    ├─ 🐳 build frontend → DockerHub
    └─ 🐳 build nginx    → DockerHub
               │
               ▼ (все три успешны)
         🚀 deploy → production server
```

### Необходимые секреты в GitHub

| Секрет | Описание |
|--------|----------|
| `DOCKER_USERNAME` | Логин DockerHub |
| `DOCKER_PASSWORD` | Пароль/токен DockerHub |
| `HOST` | IP production сервера |
| `USER` | SSH пользователь сервера |
| `SSH_KEY` | Приватный SSH ключ |
| `SSH_PASSPHRASE` | Пассфраза SSH ключа (если есть) |

---

## 📂 Структура проекта

```
foodgram/
├── backend/
│   ├── api/                    # Основное Django-приложение
│   │   ├── serializers.py      # DRF сериализаторы
│   │   ├── views.py            # ViewSets
│   │   ├── filters.py          # Фильтры рецептов/ингредиентов
│   │   ├── permission.py       # Кастомные права доступа
│   │   ├── paginator.py        # Пагинация
│   │   ├── services.py         # Бизнес-логика
│   │   └── urls.py             # URL маршруты
│   ├── recipes/                # Модели рецептов
│   │   ├── models.py           # Recipe, Tag, Ingredient, Favorite, ShoppingCart
│   │   └── admin.py            # Настройки админ-панели
│   ├── users/                  # Кастомная модель User
│   │   └── models.py           # User, Subscribe
│   ├── tests/                  # Тесты
│   │   ├── conftest.py
│   │   ├── test_models.py
│   │   ├── test_security.py
│   │   ├── test_api/
│   │   └── test_integration/
│   ├── foodgram_backend/       # Настройки Django
│   │   └── settings.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React приложение
├── infra/                      # Nginx + docker-compose (dev)
├── docs/                       # OpenAPI схема
├── data/                       # Начальные данные (ингредиенты)
├── docker-compose.production.yml
└── .env.example
```

---

## 🔒 Безопасность

- **Аутентификация** — Token Auth (djoser)
- **CORS** — настраивается через `CORS_ALLOWED_ORIGINS`
- **HTTPS** — `SECURE_SSL_REDIRECT`, `HSTS` (в production при `DEBUG=False`)
- **Заголовки** — `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`
- **Cookies** — `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` в production
- **Rate Limiting** — 200 req/day для анонимов, 2000 req/day для авторизованных
- **БД** — UniqueConstraints на всех критичных полях (БД-уровень, не только API)

---

## 👤 Автор

**Мухаммад Тагаев** — Backend-разработчик

[![GitHub](https://img.shields.io/badge/GitHub-Muta--Mad-181717?style=flat-square&logo=github)](https://github.com/Muta-Mad)
