# PulseWave

## Переменные окружения

### Postgres DB
```
DB_NAME = название БД
DB_USER = имя пользователя
DB_PASSWORD = пароль пользователя
DB_HOST = хост
DB_PORT = порт
```

### Email
```
EMAIL_HOST_USER = email адрес с когорого отправляется email
EMAIL_HOST_PASSWORD = пароль email приложения
```

### Django secret
Для локальных натроек можно использовать любой SECRET_KEY, например:

```SECRET_KEY = django-insecure-l7h7&-z_@90u@ijh#-8q%:?5g3l#593v$c_*1x%G#$2+0v@_p7```


## Установка
1. Клонируйте репозиторий на свой компьютер
2. Установите и активируйте виртуальное виртуальное окружение в папке с проектом:
```
python3 -m venv venv
source venv/bin/activate
```
3. Установите зависимости:
```
pip install -r requirements.txt
```

4. Создайте и примените миграции

    Cперва выполнить команду:

    ```
   cd pulsewave
   python3 manage.py makemigrations
   ```

    только после этого:
   
    `python3 manage.py migrate`

  
5. Запуск сервера:
   
   `python3 manage.py runserver`



## API Documentation.

    Swagger UI: `/api/schema/swagger-ui/` 
    Yaml: `/api/schema/` 
    Redoc: `/api/schema/redoc/` 


## локальные настройка
