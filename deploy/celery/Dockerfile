FROM python:3.9

WORKDIR /code
ENV PYTHONPATH=/code
COPY ./deploy/prod/req.txt /code/req.txt

RUN  pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir --upgrade -r /code/req.txt


COPY . .