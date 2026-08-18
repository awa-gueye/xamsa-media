# Déploiement de Xamsa Média sur Fly.io

Guide pas à pas pour mettre le site en ligne. Base **SQLite + médias sur un
volume persistant**, HTTPS automatique, planificateur (RSS + brief) intégré.

## 0. Préparer les outils (une seule fois)

1. Créez un compte sur https://fly.io (une carte bancaire est demandée pour
   éviter les abus ; l'usage reste ~5-6 $/mois).
2. Installez **flyctl** :
   - Windows (PowerShell) : `iwr https://fly.io/install.ps1 -useb | iex`
   - Puis connectez-vous : `fly auth login`

## 1. Générer une clé secrète Django

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Gardez la valeur affichée pour l'étape 4 (`DJANGO_SECRET_KEY`).

## 2. Créer l'application et le volume

Choisissez un nom **globalement unique** (remplacez `xamsamedia` partout, y
compris dans `fly.toml` -> `app = "..."`).

```bash
fly apps create xamsamedia
fly volumes create xamsa_data --region cdg --size 3 --yes
```
(3 Go suffisent largement au départ pour la base + les médias.)

## 3. Adapter `fly.toml`

Dans `fly.toml`, vérifiez :
- `app = "xamsamedia"` (le nom choisi)
- `DJANGO_ALLOWED_HOSTS = "xamsamedia.fly.dev"`
- `DJANGO_CSRF_TRUSTED_ORIGINS = "https://xamsamedia.fly.dev"`

## 4. Enregistrer les secrets (jamais dans le code)

```bash
fly secrets set \
  DJANGO_SECRET_KEY="collez_la_cle_de_l_etape_1" \
  GEMINI_API_KEY="votre_cle_gemini" \
  EMAIL_HOST="smtp.gmail.com" \
  EMAIL_PORT="587" \
  EMAIL_USE_TLS="1" \
  EMAIL_HOST_USER="xamsamedia@gmail.com" \
  EMAIL_HOST_PASSWORD="le_mot_de_passe_dapplication_16_car" \
  DEFAULT_FROM_EMAIL="Xamsa Média <xamsamedia@gmail.com>"
```
(Vous pouvez déployer sans les EMAIL_* : les emails s'afficheront dans les logs
au lieu d'être envoyés, tout le reste fonctionne.)

## 5. Déployer

```bash
fly deploy
```
Fly construit l'image (Dockerfile), applique les migrations au démarrage, puis
lance le site sur `https://xamsamedia.fly.dev`.

## 6. Données de départ (une seule fois)

```bash
fly ssh console
# une fois dans la machine :
python manage.py seed              # catégories, sources RSS, annuaire des médias + logos
python manage.py createsuperuser   # votre compte administrateur
exit
```
La revue de presse se remplit ensuite toute seule (ingestion toutes les 4 min),
et le brief du jour se génère automatiquement.

## 7. Brancher un nom de domaine (optionnel)

Pour `xamsamedia.com` (ou un `.sn`) :

```bash
fly certs add xamsamedia.com
fly certs add www.xamsamedia.com
```
Fly affiche les enregistrements DNS (A / AAAA / CNAME) à créer chez votre
registrar. Une fois le certificat validé, mettez à jour :

```bash
fly secrets set \
  DJANGO_ALLOWED_HOSTS="xamsamedia.com,www.xamsamedia.com,xamsamedia.fly.dev" \
  DJANGO_CSRF_TRUSTED_ORIGINS="https://xamsamedia.com,https://www.xamsamedia.com"
```
(Les variables passées en `secrets` écrasent celles de `fly.toml`.)

## Au quotidien

- Mettre à jour le site après des changements : `fly deploy`
- Voir les logs (ingestion, brief, erreurs) : `fly logs`
- Ouvrir un shell sur le serveur : `fly ssh console`
- Sauvegarder la base : `fly ssh console -C "cat /data/db.sqlite3" > sauvegarde.sqlite3`

## Points d'attention

- **Une seule machine** doit tourner (le planificateur RSS/brief y vit).
  `auto_stop_machines = "off"` et `min_machines_running = 1` dans `fly.toml`
  garantissent qu'elle reste allumée. Ne montez pas à plusieurs machines sans
  d'abord sortir le planificateur dans un worker séparé et passer à PostgreSQL.
- **Quand le trafic grandit** : migrer vers PostgreSQL géré (bloc déjà prévu et
  commenté dans `config/settings.py`) et, si besoin, stocker les médias sur un
  service objet (S3/R2). Le code est déjà paramétré par variables d'environnement.
- **Régénérez** toute clé/API qui aurait été partagée en clair.
