
FROM python:3.10-slim


WORKDIR /code


COPY ./deploy/requirements-base.txt /code
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements-base.txt

COPY ./deploy/requirements-dev.txt /code
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements-dev.txt


COPY ./ /code


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips='*'", "--proxy-headers"]


