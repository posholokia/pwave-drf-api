FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

#RUN addgroup --gid 1000 app &&  \
#    adduser --home /usr/home/web --uid 1000 --gid 1000 app
RUN useradd -u 1000 -ms /bin/bash celery

WORKDIR /usr/home/web

COPY ./requirements.txt /usr/home/web/requirements.txt

#RUN pip install --upgrade pip && \
#    pip install -r /usr/home/web/requirements.txt


COPY . /usr/home/web

USER celery

EXPOSE 8000

