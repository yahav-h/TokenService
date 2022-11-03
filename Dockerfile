FROM python:3.9

WORKDIR /app

COPY ./token_service_main.py /app/token_service_main.py
COPY ./helpers.py /app/helpers.py
COPY ./requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

EXPOSE 8000