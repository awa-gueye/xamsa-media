# Image de production Xamsa Media (Django + gunicorn + WhiteNoise).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_DEBUG=0

WORKDIR /app

# Dependances systeme (Pillow : jpeg/zlib).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x ./docker-entrypoint.sh

# Fichiers statiques compiles a la construction (servis par WhiteNoise).
RUN python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
