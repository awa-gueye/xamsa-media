#!/bin/sh
# Demarrage du conteneur : prepare le volume, applique les migrations, lance gunicorn.
set -e

# Prepare les dossiers sur le volume persistant (base + medias).
mkdir -p "$(dirname "${DJANGO_DB_PATH:-/app/db.sqlite3}")" "${DJANGO_MEDIA_ROOT:-/app/media}"

# Migrations a chaque demarrage (la base SQLite est sur le volume monte).
python manage.py migrate --noinput

# RUN_SCHEDULER=1 : ce seul processus web fait tourner l'ingestion RSS + le brief.
exec env RUN_SCHEDULER=1 gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 60
