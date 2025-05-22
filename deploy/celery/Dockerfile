FROM python:3.10-slim

WORKDIR /code
ENV PYTHONPATH=/code

COPY ./deploy/requirements-base.txt /code
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements-base.txt

COPY ./deploy/requirements-dev.txt /code
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements-dev.txt


COPY . .