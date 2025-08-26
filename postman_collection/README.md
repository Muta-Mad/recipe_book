Foodgram — это онлайн-сервис для публикации рецептов. Пользователи могут создавать свои собственные рецепты, просматривать публикации других авторов, подписываться на понравившихся кулинаров, добавлять рецепты в избранное и в список покупок, который можно удобно скачать в виде текстового файла.

🚀 Стек технологий
Бэкенд: Python 3.11, Django 4.2, Django REST Framework 3.14

База данных: PostgreSQL 13

Веб-сервер: Nginx

Контейнеризация: Docker, Docker Compose

Аутентификация: JWT (djangorestframework-simplejwt)

📦 Развертывание проекта в Docker
Клонируйте репозиторий и перейдите в него:

```
git clone git@github.com:Muta-Mad/foodgram.git
cd foodgram
```
В директории /foodgram создайте файл .env, с переменными окружения, используя образец .env.example

перейдите в директорию infra

```
cd infra
```
поднимите проект

```
docker-compose up -d --build
```

Выполните миграции, соберите статику, создайте суперпользователя
```
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend cp -r /app/collected_static/. /backend_static/static/
```
Наполните базу данных 
```
docker-compose exec backend python manage.py loaddata ingredients.json
```
проект будет доступен по адресу http://localhost:8000/


Локальный запуск (для разработки)

Активируйте виртуальное окружение и установите зависимости:

python -m venv venv
source venv/bin/activate  # для Linux/MacOS
# или
source venv/Scripts/activate  # для Windows
pip install -r requirements.txt

по умолчанию (если вы не переключите в файле .env USE_SQLITE в положение False)
проект будет работать на sqlite3

Выполните миграции:
```
python manage.py migrate
```
```
python manage.py loaddata ingredients.json
```
Убедитесь, что файл ingredients.json находится в директории backend/.
Запустите сервер:
```
python manage.py runserver
```

📖 Документация к API (Redoc)

в директории \foodgram\docs расположена документация
откройте файл openapi-schema.yml в любом из сервисов 
например https://redocly.github.io/redoc/

🧪 Примеры запросов к API

Получение токена (Аутентификация)

Запрос:
POST /api/auth/token/login/
```
{
  "email": "user@example.com",
  "password": "string"
}
```

Ответ:
```
{
  "auth_token": "your_auth_token_here"
}
```
Получение списка рецептов

Запрос:
GET /api/recipes/

Ответ (упрощенный):

```
{
  "count": 123,
  "next": "http://foodgram.host/api/recipes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 0,
      "tags": [...],
      "author": {...},
      "ingredients": [...],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.host/media/recipes/images/image.jpeg",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```

👥 Авторство

Разработано в рамках учебного курса Яндекс Практикума.
Автор бэкенда Meti.