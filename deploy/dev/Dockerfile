
FROM python:3.9


WORKDIR /code


COPY ./deploy/dev/req.txt /code/req.txt

RUN  pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir --upgrade -r /code/req.txt


COPY ./ /code


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


