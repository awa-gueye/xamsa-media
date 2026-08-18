# Xamsa Media

Plateforme de journalisme d'investigation, d'analyse des medias et de multimedia
pour le Senegal. Projet Django.

## Architecture

Trois briques distinctes :

1. Contenu editorial (app `redaction`) : enquetes, dossiers, rubriques, avec l'admin Django.
2. Veille et revue de presse (app `veille`) : agregation des sources par flux RSS.
   On ne stocke que titre + resume + lien vers la source (respect du droit d'auteur).
3. Assistant `Looy laaj ?` (app `assistant`) : endpoint de recherche dans le corpus,
   base d'un futur assistant RAG.

L'app `core` porte la page d'accueil. Le design (vert, Arial + Times New Roman,
icones SVG) vit dans `static/css/xamsa.css`.

## Demarrage rapide

```
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py seed             # donnees de demonstration
python manage.py createsuperuser  # pour acceder a /admin
python manage.py runserver
```

Ouvrez http://127.0.0.1:8000 pour l'accueil, http://127.0.0.1:8000/admin pour publier.

## Ingestion de la presse

```
python manage.py ingest --limit 15
```

Verifiez d'abord les URL de flux RSS dans /admin (section Sources). Celles fournies
par `seed` sont indicatives et doivent etre confirmees pour chaque media.

## Chatbot "Looy laaj ?" (assistant IA + RAG)

L'assistant est branche sur un vrai LLM avec recuperation de contexte (RAG) :

1. `assistant/retrieval.py` : recupere les articles et items de revue de presse
   pertinents dans la base (contenu du site).
2. `assistant/web_search.py` : recherche web via DuckDuckGo (librairie `ddgs`,
   sans cle API) pour les sources externes.
3. `assistant/llm.py` : passe ce contexte a un LLM (Google Gemini par defaut,
   appele en REST) qui redige une reponse claire en francais et cite les sources.
4. `assistant/views.py` orchestre le tout et garde le meme contrat JSON
   (`{texte, sources}`). En l'absence de cle ou en cas d'erreur du LLM, il
   retombe automatiquement sur une reponse mots-cles : le chatbot marche toujours.

Configuration (fichier `.env` a la racine, voir `.env.example`) :

- `GEMINI_API_KEY` : cle gratuite sur https://aistudio.google.com/apikey
- `GEMINI_MODEL` : `gemini-2.0-flash` par defaut
- `LLM_PROVIDER` : `gemini` (defaut) ; `anthropic` possible (installer `anthropic`)
- `WEB_SEARCH_ENABLED` : `1` (defaut) ou `0` pour se limiter au contenu du site

Installez les dependances avec `pip install -r requirements.txt` (ajoute `ddgs`).

Piste d'amelioration : pour une recherche semantique plus fine, ajouter un index
vectoriel (par ex. pgvector avec PostgreSQL) en amont du retrieval.

## Passer sur PostgreSQL

Decommentez le bloc PostgreSQL dans `config/settings.py`, installez `psycopg2-binary`,
et definissez les variables d'environnement DB_*.

## Garder l'actualite a jour (Mur de la presse et A la Une)

Le Mur de la presse et la section A la Une affichent les items les plus recents
de la revue de presse. Ils ne se rafraichissent que lorsque l'ingestion tourne.
Pour qu'ils restent "en direct", planifiez la commande d'ingestion :

- Windows (Planificateur de taches) : creez une tache qui execute, toutes les
  15-30 minutes, `python manage.py ingest` dans le dossier du projet
  (avec l'environnement virtuel active).
- Linux/macOS (cron) : `*/20 * * * * cd /chemin/projet && .venv/bin/python manage.py ingest`

Sans planification, relancez `python manage.py ingest` manuellement pour voir
arriver de nouvelles unes.

## Structure des ecrans

- A la Une : dernieres nouvelles + recherche + Mur de la presse.
- Actualites : poles editoriaux + rubrique speciale "Medias du Senegal".
- Dossiers : nos productions + curation de presse (+ Audio & Video).
- Academie : cours, formations, webinaires, ressources, certifications.
- Communaute : contribution, concours, associations de presse, opportunites.
- Recherche : sur les publications, la revue et tous les espaces.

Les espaces Academie, Communaute et Medias du Senegal sont pilotes par les
modeles de l'app `espaces` (editables dans /admin).

## Ingestion AUTOMATIQUE (nouveau)

Quand le serveur tourne (`python manage.py runserver`), l'ingestion se lance
toute seule en arriere-plan toutes les 4 minutes : l'actualite se met a jour
sans rien faire. Le navigateur, lui, rafraichit le carrousel et le Mur de la
presse toutes les 30 secondes. La date, l'heure et les titres avancent donc
automatiquement au fil des publications des sources.

- Texte nettoye (entites HTML decodees, balises retirees, accents corrects).
- Images en haute resolution (og:image de l'article source) pour eviter le flou.

En production (gunicorn), preferez une tache planifiee (cron) plutot que le
thread : `*/5 * * * * cd /projet && .venv/bin/python manage.py ingest`.
