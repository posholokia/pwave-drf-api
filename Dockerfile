FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

RUN useradd -u 1000 -ms /bin/bash celery

WORKDIR /usr/home/web

COPY ./requirements.txt /usr/home/web/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /usr/home/web/requirements.txt


COPY . /usr/home/web

USER celery

EXPOSE 8000

ENTRYPOINT [ "python3" ]
CMD [ "-m", "gunicorn", "-b", "0.0.0.0:8080", "--workers", "1", "--access-logfile", "-",  "pulsewave.asgi", "--reload", "-k", "uvicorn.workers.UvicornWorker" ]


