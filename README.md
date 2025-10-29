# :file_folder: chef_space

![example workflow](https://github.com/vladiswave/chef_space/actions/workflows/main.yml/badge.svg)

## :scroll: Описание
**ChefSpace** — это платформа для любителей кулинарии, где пользователи могут делиться своими рецептами, сохранять понравившиеся рецепты в избранное и подписываться на обновления других авторов. Зарегистрированные участники получают доступ к удобному сервису «Список покупок», который помогает составлять перечень продуктов для приготовления выбранных блюд.

## :globe_with_meridians: Используемые технологии
- Python 3.9
- Django 3.2
- Django REST Framework
- Djoser
- Docker
- Nginx

## :computer: Как запустить проект

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/vladiswave/chef_space
```

* Создайте в корне проекта и заполните файл .env. В качестве примера ориентируйтесь на файл [.env.example](/.env.example):
    * ALLOWED_HOSTS - IP и доменное имя сервера
    * DB_NAME - имя БД
    * POSTGRES_DB=food
    * POSTGRES_PASSWORD=food_password
    * POSTGRES_USER=food_user
    * SECRET_KEY - секретный ключ django проекта
    * USE_SQLITE=False
    * DEBUG=False

* На ```https://github.com/<your_name>/chef_space/actions``` нужно задать:
    * DOCKER_PASSWORD - пароль от Docker
    * DOCKER_USERNAME - имя пользователя в Docker
    * HOST - ваш IP сервера
    * SSH_KEY - закрытый ключ для подключения к серверу
    * SSH_PASSPHRASE - пароль к закрытому ключу
    * TELEGRAM_TO - ID вашего телеграм-аккаунта
    * TELEGRAM_TOKEN - ключ вашего бота в телеграм
    * USER - имя пользователя на сервере

* Настройте внешний Nginx на вашем удаленном сервере и создайте папку /infra/ внутри проекта

* Сделайте любой push на github, и проект будет запущен на вашем сервере

* Реализована команда для добавления данных json формата в БД:
```
python manage.py add_data_from_json
```

## Пример запроса
### Post-запрос для рецепта произведению c id=8:

```
GET /api/recipes/
```

#### Тело запроса:

```
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

#### Ответ:

```
{
  "id": 0,
  "tags": [
    {
      "id": 0,
      "name": "Завтрак",
      "slug": "breakfast"
    }
  ],
  "author": {
    "email": "user@example.com",
    "id": 0,
    "username": "pEo1S96taL5KRBfdT+oc@uzFq+1ORVzHn_fBxguV3kP7BkSB3ZJT6gYoqSIvlKMkjz",
    "first_name": "Вася",
    "last_name": "Иванов",
    "is_subscribed": false,
    "avatar": "http://chef_space.example.org/media/users/image.png"
  },
  "ingredients": [
    {
      "id": 0,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 1
    }
  ],
  "is_favorited": true,
  "is_in_shopping_cart": true,
  "name": "string",
  "image": "http://chef_space.example.org/media/recipes/images/image.png",
  "text": "string",
  "cooking_time": 1
}
```

## :books: Документация проекта
Техническая документация API проекта ChefSpace расположена в файле 
[redoc.yaml](docs/redoc.html).

## :busts_in_silhouette: Автор

[**Владислав Филиппов**](https://github.com/vladiswave)
