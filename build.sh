#!/usr/bin/env bash
# Etapes de build executees par Render a chaque deploiement.
set -o errexit

pip install -r requirements.txt

# Fichiers statiques (servis par WhiteNoise).
python manage.py collectstatic --no-input

# Base de donnees : applique les migrations.
python manage.py migrate

# Donnees structurelles reelles (idempotent) : categories, sources RSS,
# annuaire des medias senegalais + import automatique des logos.
python manage.py seed

# Compte administrateur (sans shell) : cree depuis ADMIN_EMAIL / ADMIN_PASSWORD.
python manage.py creer_admin
