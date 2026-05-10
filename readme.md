# TeamFinder

TeamFinder - приложение для поиска команды на pet-проекты.
Пользователь может опубликовать идею, указать нужные навыки, собрать участников
и посмотреть профили других разработчиков.

В репозитории реализован вариант 3 задания: базовый TeamFinder, навыки проектов
и фильтрация списка проектов по выбранному навыку.



## Запуск локально

Создайте окружение и установите зависимости:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Поднимите PostgreSQL:

```bash
docker compose up -d
```

По умолчанию база слушает `localhost:5436`. Эти значения уже совпадают с
настройками Django и `.env_example`, поэтому для обычного локального запуска
копировать `.env` необязательно.

Примените миграции и добавьте демо-данные:

```bash
python manage.py migrate
python manage.py seed_demo
```

Запустите сервер:

```bash
python manage.py runserver
```

Откройте [http://localhost:8000](http://localhost:8000).

## Демо-аккаунт

После `python manage.py seed_demo` можно войти под пользователем:

```text
email: maria@yandex.ru
password: password
```

Команду `seed_demo` можно запускать повторно. Она не создаёт дубли пользователей,
проектов и навыков.

Демо-набор хранится в `projects/fixtures/demo_data.json`. Если нужно проверить
другие данные, можно передать свой JSON-файл:

```bash
python manage.py seed_demo --data-file path/to/demo_data.json
```

## Проверка

```bash
python manage.py check
python manage.py test
```

## Заметки по проекту

- Основные шаблоны лежат в `templates/`.
- Статика находится в `static/`, загруженные аватары - в `media/avatars/`.
- `requirements.txt` сохранён в UTF-8.
- `psycopg2-binary` закреплён на `2.9.12`: эта версия ставится готовым wheel
  на Python 3.14 и не требует локальный `pg_config`.

## Контакты

- GitHub: [kirbysss369](https://github.com/kirbysss369)
- Email: [tretiakpavel13@gmail.com](mailto:tretiakpavel13@gmail.com)
