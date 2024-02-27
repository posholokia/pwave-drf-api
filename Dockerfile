FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

RUN useradd -u 1000 -ms /bin/bash app
WORKDIR /app

COPY . .

RUN chown -R app:app /app

USER app



RUN set -ex &&\
    export TMPDIR='/var/tmp' &&\
    python3 -m pip install --no-cache-dir --no-warn-script-location --upgrade pip &&\
    python3 -m pip install --no-cache-dir --no-warn-script-location --user -r requirements.txt

EXPOSE 8000

ENTRYPOINT [ "python3" ]
CMD [ "-m", "gunicorn", "-b", "0.0.0.0:8000", "--workers", "1", "--access-logfile", "-",  "pulsewave.asgi", "--reload", "-k", "uvicorn.workers.UvicornWorker" ]
