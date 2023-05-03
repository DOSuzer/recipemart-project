![example workflow](https://github.com/dosuzer/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)

Сервер: 158.160.30.120 / uzer.webhop.me (без HTTPS)

Админка: sh@ya.ru
Пароль:  slanara33

## Проект Foodgram
Foodgram - продуктовый помощник с базой кулинарных рецептов. Позволяет публиковать рецепты, подписываться на любимых авторов, сохранять рецепты в избранные, формировать список покупок для выбранных рецептов.
Документация по API доступна по адресу 158.160.30.120/api/docs/

### Запуск проекта на удаленном сервере:

- Клонировать репозиторий:
```
https://github.com/DOSuzer/foodgram-project-react.git
```

- Установить на сервере Docker, Docker Compose:

```
sudo apt install curl                                   # установка утилиты для скачивания файлов
curl -fsSL https://get.docker.com -o get-docker.sh      # скачать скрипт для установки
sh get-docker.sh                                        # запуск скрипта
sudo apt-get install docker-compose-plugin              # последняя версия docker compose
```

- Скопировать на сервер файлы docker-compose.yml, nginx.conf из папки infra (команды выполнять находясь в папке infra):

```
scp docker-compose.yml nginx.conf username@IP:~         # username - имя пользователя на сервере
                                                        # IP - публичный IP сервера
```

- В домашней папке на сервере создайте файл .env:

```
DB_ENGINE=django.db.backends.postgresql   # указываем, что работаем с postgresql
DB_NAME=postgres                          # имя базы данных
POSTGRES_USER=postgres                    # логин для подключения к базе данных
POSTGRES_PASSWORD=password                # пароль для подключения к БД (установите свой)
DB_HOST=db                                # название сервиса (контейнера)
DB_PORT=5432                              # порт для подключения к БД
```

- Создать и запустить контейнеры Docker, выполнить команду на сервере
*(версии команд "docker compose" или "docker-compose" отличаются в зависимости от установленной версии Docker Compose):*
```
sudo docker compose up -d
```

- После успешной сборки выполнить миграции:
```
sudo docker compose exec backend python manage.py migrate
```

- Создать суперпользователя:
```
sudo docker compose exec backend python manage.py createsuperuser
```

- Собрать статику:
```
sudo docker compose exec backend python manage.py collectstatic --no-input
```

- Наполнить базу данных содержимым из файла ingredients.csv:
```
sudo docker compose exec backend python manage.py import_ingredients
```

- Для остановки контейнеров Docker:
```
sudo docker compose down -v      # с их удалением
sudo docker compose stop         # без удаления
```
### Для работы с GitHub Actions необходимо в репозитории в разделе Settings > Secrets and variables > Actions создать переменные окружения:
```
SECRET_KEY              # секретный ключ Django проекта
DOCKER_USERNAME         # логин Docker Hub
DOCKER_PASSWORD         # пароль от Docker Hub
HOST                    # публичный IP сервера
USER                    # имя пользователя на сервере
SSH_KEY                 # приватный ssh-ключ
PASSPHRASE              # *если ssh-ключ защищен паролем
TELEGRAM_TO             # ID телеграм-аккаунта для отправки сообщения
TELEGRAM_TOKEN          # токен бота, посылающего сообщение

DB_ENGINE               # django.db.backends.postgresql
DB_NAME                 # postgres
POSTGRES_USER           # пользователь postgres
POSTGRES_PASSWORD       # пароль postgres
DB_HOST                 # db
DB_PORT                 # 5432 (порт по умолчанию)
```
### После каждого обновления репозитория (push в ветку master) будет происходить:

1. Проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
2. Сборка и доставка докер-образов frontend и backend на Docker Hub
3. Разворачивание проекта на удаленном сервере
4. Отправка сообщения в Telegram в случае успеха