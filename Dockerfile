FROM python:3.9.12-slim

RUN addgroup --gid 1000 app &&\     
    adduser --home /app --uid 1000 --gid 1000 app

WORKDIR /app

COPY . .

RUN chown -R app:app /app

USER app

RUN set -ex &&\
    python3 -m pip install --no-cache-dir --no-warn-script-location --upgrade pip &&\
    python3 -m pip install --no-cache-dir --no-warn-script-location --user -r requirements.txt

ENTRYPOINT [ "python3", "-m", "gunicorn", "-b", "0.0.0.0:8080", "--workers", "4", "--access-logfile", "'-'",  "pulsewave.wsgi", "--reload" ]
#ENTRYPOINT [ "python3", "manage.py", "runserver", "0.0.0.0:8080" ]

