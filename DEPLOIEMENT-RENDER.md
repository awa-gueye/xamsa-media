# Déployer Xamsa Média gratuitement sur Render

Render est la meilleure option gratuite pour une application Django (Netlify ne
fait tourner que du statique ; Railway n'a plus de vrai palier gratuit).

Ce que Render fournit gratuitement : un **service web** + une base **PostgreSQL**.
Tout est déjà préparé dans le dépôt (`render.yaml`, `build.sh`, config prod).

---

## 1. Mettre le code sur GitHub

Render déploie depuis un dépôt Git. Depuis le dossier du projet :

```bash
git init
git add .
git commit -m "Xamsa Media - pret pour deploiement"
```

Créez un dépôt sur https://github.com/new (par ex. `xamsa-media`, privé ou
public), puis :

```bash
git remote add origin https://github.com/VOTRE-COMPTE/xamsa-media.git
git branch -M main
git push -u origin main
```

> Le fichier `.env` et la base locale `db.sqlite3` ne sont PAS envoyés
> (protégés par `.gitignore`). Les secrets se règlent dans Render (étape 3).

## 2. Créer le service sur Render (Blueprint)

1. Créez un compte gratuit sur https://render.com (connexion avec GitHub).
2. Cliquez **New +** → **Blueprint**.
3. Sélectionnez votre dépôt `xamsa-media`. Render lit `render.yaml` et propose
   de créer : un service web `xamsa-media` + une base `xamsa-db` (PostgreSQL).
4. Cliquez **Apply**. Render lance le **build** (`build.sh` : installe les
   dépendances et collecte le statique), puis au **démarrage** (`start.sh`)
   applique les migrations, insère les données réelles + logos et crée l'admin.
   (Les opérations base de données sont au démarrage, pas au build : le PostgreSQL
   interne de Render n'est joignable qu'au runtime.)

## 3. Renseigner les secrets

Dans le service `xamsa-media` → onglet **Environment**, renseignez les variables
marquées « à définir » :

| Variable | Valeur |
|---|---|
| `GEMINI_API_KEY` | votre clé Gemini (https://aistudio.google.com/apikey) |
| `EMAIL_HOST_PASSWORD` | le mot de passe d'application Gmail (xamsamedia@gmail.com) |
| `CLOUDINARY_URL` | l'URL Cloudinary (voir « Fichiers envoyés » ci-dessous) |
| `ADMIN_EMAIL` | l'email de l'administrateur (ex. xamsamedia@gmail.com) |
| `ADMIN_PASSWORD` | un mot de passe administrateur fort |

(La clé secrète Django, l'URL de la base et le domaine sont configurés
automatiquement.) Enregistrez : Render redéploie.

## 4. Le compte administrateur (aucun shell nécessaire)

Le palier gratuit de Render **ne donne pas accès au Shell/SSH** : la commande
interactive `createsuperuser` n'est donc pas utilisable. C'est déjà géré : au
démarrage, `start.sh` lance `python manage.py creer_admin`, qui **crée
l'administrateur** à partir des variables `ADMIN_EMAIL` et `ADMIN_PASSWORD`
renseignées à l'étape 3.

- Le compte n'est créé qu'une seule fois (idempotent) : les redéploiements
  suivants n'écrasent pas son mot de passe.
- Vous vous connectez ensuite sur le site avec cet email et ce mot de passe, et
  l'administration est accessible sur `/admin/`.
- Si vous oubliez le mot de passe, utilisez « Mot de passe oublié ? » sur la page
  de connexion (l'email de réinitialisation part via xamsamedia@gmail.com).

Votre site est en ligne à l'adresse `https://xamsa-media.onrender.com`
(le nom exact est affiché en haut du service).

---

## Bon à savoir (palier gratuit)

- **Mise en veille** : le service s'endort après 15 min sans visite ; la
  première visite suivante prend ~30 à 60 s (réveil). La revue de presse RSS et
  le brief du jour se rafraîchissent quand il y a du trafic.
- **Base PostgreSQL gratuite** : expire après 30 jours sur Render. Pour une base
  gratuite durable, créez-en une sur https://neon.tech (gratuit, sans expiration)
  et collez son URL dans la variable `DATABASE_URL` — aucun changement de code.
- **Fichiers envoyés** (photos de profil, images des contributions, logos) :
  réglé via **Cloudinary** (voir ci-dessous). Sans lui, ils seraient perdus à
  chaque redéploiement (pas de disque persistant gratuit).

## Fichiers envoyés permanents (Cloudinary, gratuit)

Le palier gratuit de Render n'a pas de disque persistant : les fichiers envoyés
seraient effacés à chaque redéploiement. La solution : les stocker sur
**Cloudinary** (offre gratuite, 25 Go), servis par son CDN.

1. Créez un compte gratuit sur https://cloudinary.com
2. Sur le **Dashboard**, copiez la valeur **API Environment variable** — c'est une
   URL de la forme `cloudinary://<api_key>:<api_secret>@<cloud_name>`.
3. Dans Render → service `xamsa-media` → **Environment**, collez-la dans la
   variable `CLOUDINARY_URL`. Enregistrez (Render redéploie).

C'est tout : dès que `CLOUDINARY_URL` est présent, toutes les images envoyées
(profils, contributions) et les logos des médias sont stockés durablement sur
Cloudinary. Sans cette variable, l'application utilise le disque local (pratique
en développement). Aucun changement de code, aucun risque : c'est automatique.

## Redéployer après une modification

```bash
git add .
git commit -m "Mise a jour"
git push
```

Render redéploie automatiquement à chaque `push`.
