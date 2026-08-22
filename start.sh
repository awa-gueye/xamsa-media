#!/usr/bin/env bash
# Demarrage (Render) : execute au RUNTIME, ou le PostgreSQL interne est joignable.
set -o errexit

# Base de donnees : migrations (idempotent).
python manage.py migrate --no-input

# Donnees structurelles reelles (idempotent) : categories, sources RSS,
# annuaire des medias senegalais + import des logos.
python manage.py seed

# Compte administrateur depuis ADMIN_EMAIL / ADMIN_PASSWORD (idempotent).
python manage.py creer_admin

# Serveur WSGI de production. RUN_SCHEDULER=1 (uniquement ici, pas pour migrate/
# seed) active la veille RSS + le brief dans le process gunicorn.
# exec : gunicorn devient le process principal (bonne gestion des signaux).
exec env RUN_SCHEDULER=1 gunicorn config.wsgi:application --bind "0.0.0.0:$PORT" --workers 1 --threads 4 --timeout 60
