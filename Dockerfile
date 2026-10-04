FROM python:3.11-alpine

WORKDIR /opt

RUN apk add --no-cache g++ && rm -rf /var/cache/apk/*

RUN pip3 install --upgrade pip poetry

COPY pyproject.toml poetry.lock /opt/
COPY app /opt/app

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi
