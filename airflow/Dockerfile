FROM apache/airflow:3.0.0

USER root
RUN apt-get update && \
    apt-get install -y \
        libgdal-dev \
        python3-gdal \
        libgeos-dev \
        libproj-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/models && \
    chown airflow:root /app/models

# Возвращаемся к пользователю airflow
USER airflow

# Установка Python-пакетов
RUN pip install --no-cache-dir \
    pandas \
    sqlalchemy \
    psycopg2-binary


COPY requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt



USER airflow
