FROM python:3.9

WORKDIR /app

COPY ./resources /app/resources
COPY ./resources/properties.yml /app/resources/properties.yml
COPY ./pages /app/pages
COPY ./pages/__init__.py /app/pages/__init__.py
COPY ./pages/goog_login_page.py /app/pages/goog_login_page.py
COPY ./pages/mso_login_page.py /app/pages/mso_login_page.py
COPY ./token_service_main.py /app/token_service_main.py
COPY ./helpers.py /app/helpers.py
COPY ./dto.py /app/dto.py
COPY ./dao.py /app/dao.py
COPY ./database.py /app/database.py
COPY ./requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

EXPOSE 8000