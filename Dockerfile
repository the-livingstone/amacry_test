FROM python:3.11-alpine

WORKDIR /opt

RUN apk add nano curl g++ && rm -rf /var/cache/apk/*

RUN pip3 install --upgrade pip poetry

COPY .env poetry.lock pyproject.toml /opt/

RUN poetry config virtualenvs.create false
RUN poetry install --only main --no-interaction --no-ansi