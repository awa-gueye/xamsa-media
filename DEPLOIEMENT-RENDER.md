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
4. Cliquez **Apply**. Render lance le build (installe, collecte le statique,
   applique les migrations, insère les données réelles et les logos).

## 3. Renseigner les secrets

Dans le service `xamsa-media` → onglet **Environment**, renseignez les variables
marquées « à définir » :

| Variable | Valeur |
|---|---|
| `GEMINI_API_KEY` | votre clé Gemini (https://aistudio.google.com/apikey) |
| `EMAIL_HOST_PASSWORD` | le mot de passe d'application Gmail (xamsamedia@gmail.com) |

(La clé secrète Django, l'URL de la base et le domaine sont configurés
automatiquement.) Enregistrez : Render redéploie.

## 4. Créer le compte administrateur

Une fois le déploiement « Live », ouvrez le service → onglet **Shell** et lancez :

```bash
python manage.py createsuperuser
```

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
- **Fichiers envoyés** (photos de profil, images des contributions) : le palier
  gratuit n'a pas de disque persistant, ils sont perdus à chaque redéploiement.
  Les logos des médias, eux, sont régénérés automatiquement à chaque build.
  Pour rendre les envois permanents, brancher un stockage cloud gratuit
  (ex. Cloudinary) — à faire dans un second temps.

## Redéployer après une modification

```bash
git add .
git commit -m "Mise a jour"
git push
```

Render redéploie automatiquement à chaque `push`.
