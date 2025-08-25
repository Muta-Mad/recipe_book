Foodgram
Ваша кулинарная социальная сеть.
Создано, чтобы делиться вкусом!

Открыть проект > https://foodgram-yandex.ddns.net

Foodgram — это онлайн-платформа для публикации и обмена рецептами. Добавляйте свои рецепты, добавляйте понравившиеся в избранное, подписывайтесь на авторов и легко составлять список покупок для выбранных блюд.

Быстрый старт (Развертывание в контейнерах)
Проект готов к запуску в Docker-контейнерах.

Клонируйте репозиторий:
```
bash
git clone git@github.com:Muta-Mad/foodgram.git
cd foodgram/infra
```
Подготовьте окружение:

Создайте и заполните файл .env в папке infra/ на основе примера (.env.example).

Убедитесь, что порты 80, 5432 и 8000 свободны.

Запустите сборку и запуск контейнеров:
```
bash
docker-compose up -d --build
```

Выполните первоначальную настройку:
Примените миграции, соберите статику и создайте суперпользователя:
```
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend cp -r /app/collected_static/. /backend_static/static/
```

Готово!

Проект будет доступен по адресу: http://localhost
Стандартная админ-панель Django: http://localhost/admin