# Déployer Xamsa Média gratuitement sur Render

Render est la meilleure option gratuite pour une application Django (Netlify ne
fait tourner que du statique ; Railway n'a plus de vrai palier gratuit).

Render fournit gratuitement le **service web**. Pour la base de données, on
utilise **Neon** (PostgreSQL gratuit, sans expiration) plutôt que la base
managée de Render : son nom d'hôte est **public**, donc toujours résolvable —
la base interne de Render (`dpg-xxx-a`) provoque des erreurs « could not
translate host name » au runtime sur le palier gratuit.

Tout est déjà préparé dans le dépôt (`render.yaml`, `build.sh`, `start.sh`, config prod).

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

## 2. Créer la base de données (Neon, gratuit)

1. Compte gratuit sur https://neon.tech (connexion avec GitHub).
2. **Create project** (choisissez une région proche, ex. Europe). Neon crée une
   base et affiche une **Connection string**.
3. Copiez cette URL (forme `postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require`).
   Gardez-la pour l'étape 4.

## 3. Créer le service sur Render (Blueprint)

1. Créez un compte gratuit sur https://render.com (connexion avec GitHub).
2. Cliquez **New +** → **Blueprint**.
3. Sélectionnez votre dépôt `xamsa-media`. Render lit `render.yaml` et propose de
   créer le service web `xamsa-media`.
4. Cliquez **Apply**. Render lance le **build** (`build.sh` : dépendances +
   statique), puis au **démarrage** (`start.sh`) applique les migrations, insère
   les données réelles + logos et crée l'admin.

## 4. Renseigner les secrets

Dans le service `xamsa-media` → onglet **Environment**, renseignez :

| Variable | Valeur |
|---|---|
| `DATABASE_URL` | l'URL Neon copiée à l'étape 2 (`postgresql://...?sslmode=require`) |
| `GEMINI_API_KEY` | votre clé Gemini (https://aistudio.google.com/apikey) |
| `EMAIL_HOST_PASSWORD` | le mot de passe d'application Gmail (xamsamedia@gmail.com) |
| `CLOUDINARY_URL` | l'URL Cloudinary (voir « Fichiers envoyés » ci-dessous) |
| `ADMIN_EMAIL` | l'email de l'administrateur (ex. xamsamedia@gmail.com) |
| `ADMIN_PASSWORD` | un mot de passe administrateur fort |

(La clé secrète Django, l'URL de la base et le domaine sont configurés
automatiquement.) Enregistrez : Render redéploie.

## 5. Le compte administrateur (aucun shell nécessaire)

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
- **Base de données (Neon)** : gratuite et sans expiration. Son nom d'hôte public
  évite les erreurs « could not translate host name » de la base interne de Render.
  Pour changer de base, il suffit de modifier `DATABASE_URL` — aucun code à toucher.
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
