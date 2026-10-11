#!/usr/bin/env bash
# Demarrage (Render) : execute au RUNTIME, ou le PostgreSQL interne est joignable.
set -o errexit

# Base de donnees : migrations (necessaire AVANT de servir ; quasi-instantane
# quand il n'y a pas de nouvelle migration, ex. au reveil).
python manage.py migrate --no-input

# Taches lourdes et idempotentes (seed des donnees + import logos + compte admin)
# lancees EN ARRIERE-PLAN : le site repond immediatement sans les attendre.
# -> demarrage/reveil beaucoup plus rapide.
( python manage.py seed && python manage.py creer_admin ) &

# Serveur WSGI de production. RUN_SCHEDULER=1 (uniquement ici) active la veille
# RSS + le brief. exec : gunicorn devient le process principal (signaux).
exec env RUN_SCHEDULER=1 gunicorn config.wsgi:application --bind "0.0.0.0:$PORT" --workers 1 --threads 4 --timeout 60
