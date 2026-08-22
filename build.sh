#!/usr/bin/env bash
# Etapes de BUILD (Render) : PAS d'acces base de donnees ici -- le nom d'hote
# interne du PostgreSQL n'est resolvable qu'au runtime. Les migrations, le seed
# et la creation de l'admin sont faits au demarrage (voir start.sh).
set -o errexit

pip install -r requirements.txt

# Fichiers statiques (servis par WhiteNoise). N'a pas besoin de la base.
python manage.py collectstatic --no-input
