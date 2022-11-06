FROM python:3.9

WORKDIR /app

COPY ./token_service_main.py /app/token_service_main.py
COPY ./helpers.py /app/helpers.py
COPY ./requirements.txt /app/requirements.txt
COPY ./logs/runtime.log /app/logs/runtime.log


RUN pip install -r /app/requirements.txt

EXPOSE 8000