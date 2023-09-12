# PulseWave


## Установка:
1. Клонируйте репозиторий на свой компьютер
2. Установите и активируйте виртуальное виртуальное окружение в папке с проектом:
```
python3 -m venv venv
source venv/bin/activate
```
3. Установите зависимости:
```
cd pulsewave
pip install -r requirements.txt
```

4. Создайте и примените миграции

    Cперва выполнить команду:

    `python3 manage.py makemigrations`

    только после этого:
   
    `python3 manage.py migrate`

  
5. Запуск сервера:

    `python3 manage.py runserver`


## API Documentation.

    Swagger UI: `/api/schema/swagger-ui/` 
    Yaml: `/api/schema/` 
    Redoc: `/api/schema/redoc/` 


