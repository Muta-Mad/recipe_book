> **🌐 [Открыть проект →](https://foodgram-yandex.ddns.net)**

Foodgram — это онлайн-платформа для публикации и обмена рецептами. Добавляйте свои рецепты, добавляйте понравившиеся в избранное, подписывайтесь на авторов и легко составляйте список покупок для выбранных блюд.

## 🚀 Быстрый старт (Развертывание в контейнерах)

Проект готов к запуску в Docker-контейнерах.

1.  **Клонируйте репозиторий:**
    ```bash
    git clone git@github.com:Muta-Mad/foodgram.git
    cd foodgram/infra
    ```

2.  **Подготовьте окружение:**
    *   Создайте и заполните файл `.env` в папке `infra/` на основе примера (`.env.example`).
    *   Убедитесь, что порты 80, 5432 и 8000 свободны.

3.  **Запустите сборку и запуск контейнеров:**
    ```bash
    docker-compose up -d --build
    ```

4.  **Выполните первоначальную настройку:**
    ```bash
    docker-compose exec backend python manage.py migrate
    docker-compose exec backend python manage.py collectstatic --no-input
    docker-compose exec backend python manage.py createsuperuser
    docker-compose exec backend cp -r /app/collected_static/. /backend_static/static/
    ```
5. **(Опционально) Наполните базу данных начальными данными:**

Чтобы загрузить предустановленный список ингредиентов, выполните:
    ```bash
   docker-compose exec backend python manage.py load_data
    ```
6. **Готово!:**
    Проект будет доступен по адресу: **`http://localhost:8000`**
    Стандартная админ-панель Django: **`http://localhost:8000/admin`**

7.  **Как открыть документацию?:**
    Документация автоматически генерируется на основе файла openapi-schema.yml с помощью ReDoc.
    Вы также можете просмотреть схему API вручную, открыв файл foodgram/docs/openapi-schema.yml
    через онлайн-сервисы например https://redocly.github.io/redoc/
8.  **Примеры API-запросов:**
    Получение токена аутентификации 
    **Запрос:**
    POST http://localhost/api/auth/token/login/
    Body (JSON):
    {
      "email": "user@example.com",
      "password": "your_password"
    }
    **Ответ**
    {
      "auth_token": "ваш токен"
    }
## 🛠 Технологии

*   **Backend:** Django REST Framework (DRF), Djoser
*   **Frontend:** React
*   **База данных:** PostgreSQL
*   **Веб-сервер:** Nginx
*   **Контейнеризация:** Docker, Docker-compose
*   **CI/CD:** GitHub Actions

**Авторство:**
    Тагаев Мухаммад — Backend-разработчик (Python/Django)
    Яндекс.Практикум — учебный проект в рамках курса «Python-разработчик».
    Команда Yandex.Praktikum — предоставление готового фронтенда на React.