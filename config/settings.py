"""Configuration Django de Xamsa Media."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Charge les variables d'un fichier .env a la racine (cle API, etc.) si present.
try:
    from dotenv import load_dotenv
    # override=True : le .env fait autorite (evite qu'une ancienne valeur reste en
    # memoire du processus apres modification du fichier).
    load_dotenv(BASE_DIR / '.env', override=True)
except ImportError:  # python-dotenv non installe : on lit l'environnement systeme.
    pass

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-a-changer-en-production')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = ['*'] if DEBUG else [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
# Origines de confiance pour le CSRF (formulaires) en HTTPS : ex.
# "https://xamsa.fly.dev,https://xamsamedia.com"
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

# Render fournit automatiquement le domaine du service (xxx.onrender.com).
_RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if _RENDER_HOST:
    ALLOWED_HOSTS.append(_RENDER_HOST)
    CSRF_TRUSTED_ORIGINS.append('https://' + _RENDER_HOST)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps du projet
    'core',
    'redaction',
    'veille',
    'assistant',
    'multimedia',
    'espaces',
    'comptes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise sert les fichiers statiques directement (pas besoin de CDN).
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'comptes.context_processors.notifications',
                'comptes.context_processors.chatbot_suggestions',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Base de donnees.
# - En production (Render, etc.) : definir DATABASE_URL (PostgreSQL) -> persistant.
# - Sinon : SQLite local (DJANGO_DB_PATH pour pointer vers un volume si besoin).
_DATABASE_URL = os.environ.get('DATABASE_URL', '')
if _DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(_DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.environ.get('DJANGO_DB_PATH', str(BASE_DIR / 'db.sqlite3')),
            'OPTIONS': {'timeout': 20},
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise : compression des fichiers statiques (cache-busting deja gere par ?v=).
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

MEDIA_URL = 'media/'
# En production, DJANGO_MEDIA_ROOT pointe vers le volume persistant (ex. /data/media).
MEDIA_ROOT = os.environ.get('DJANGO_MEDIA_ROOT', str(BASE_DIR / 'media'))

# --- Stockage permanent des fichiers envoyes (Cloudinary) ---
# Sur un hebergeur sans disque persistant (Render gratuit), les fichiers envoyes
# (photos de profil, images des contributions, logos) seraient perdus a chaque
# redeploiement. Si CLOUDINARY_URL est defini, ils sont stockes durablement sur
# Cloudinary (offre gratuite) et servis par son CDN. Sinon : disque local (dev).
# CLOUDINARY_URL a la forme : cloudinary://<api_key>:<api_secret>@<cloud_name>
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
if CLOUDINARY_URL:
    INSTALLED_APPS += ['cloudinary', 'cloudinary_storage']
    STORAGES['default'] = {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Securite en production (actif seulement quand DEBUG=0) ---
if not DEBUG:
    # Fly.io / proxy termine le TLS et transmet X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SSL_REDIRECT', '1') == '1'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# --- Assistant "Looy laaj ?" (chatbot IA + RAG) ---------------------------
# Fournisseur LLM : 'gemini' par defaut (niveau gratuit Google AI Studio).
# L'architecture reste agnostique : changez LLM_PROVIDER sans toucher au code.
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'gemini')

# Google Gemini (appel via API REST, aucune librairie supplementaire requise).
# Cle gratuite : https://aistudio.google.com/apikey
# gemini-flash-lite-latest : le plus rapide (repond en ~1.5s). Les noms versionnes
# (gemini-2.5-flash...) peuvent renvoyer 404 selon la cle : preferer les alias -latest.
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-flash-lite-latest')

# Groq (API compatible OpenAI, tres rapide, free tier genereux et global).
# Cle gratuite : https://console.groq.com/keys  ->  mettre LLM_PROVIDER=groq
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')

# Anthropic (optionnel, si LLM_PROVIDER=anthropic). Jamais de cle en dur.
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# Recherche web (sources externes) via DuckDuckGo, sans cle. Mettre a 0 pour
# limiter l'assistant au seul contenu du site.
WEB_SEARCH_ENABLED = os.environ.get('WEB_SEARCH_ENABLED', '1') == '1'
ASSISTANT_MAX_WEB_RESULTS = int(os.environ.get('ASSISTANT_MAX_WEB_RESULTS', '3'))
ASSISTANT_MAX_SITE_RESULTS = int(os.environ.get('ASSISTANT_MAX_SITE_RESULTS', '5'))
# Backend web unique = plus rapide (le defaut de ddgs interroge tous les moteurs).
# On peut mettre une liste separee par des virgules pour un secours (plus lent).
ASSISTANT_WEB_BACKEND = os.environ.get('ASSISTANT_WEB_BACKEND', 'duckduckgo')
# Plafond de temps (secondes) pour la recherche web : au-dela, on repond sans elle.
ASSISTANT_WEB_TIMEOUT = float(os.environ.get('ASSISTANT_WEB_TIMEOUT', '4'))

LOGIN_URL = 'connexion'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# --- Email (reinitialisation du mot de passe) ---
# Envoi reel des que EMAIL_HOST est defini dans .env (ex. Gmail : smtp.gmail.com).
# Sinon : backend console (l'email s'affiche dans le terminal, zero config).
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', '0') == '1'
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '0' if EMAIL_USE_SSL else '1') == '1'
    EMAIL_TIMEOUT = 20
    # Pour Gmail, l'expediteur DOIT etre l'adresse authentifiee (sinon spam/refus).
    DEFAULT_FROM_EMAIL = (os.environ.get('DEFAULT_FROM_EMAIL')
                          or 'Xamsa Média <{}>'.format(EMAIL_HOST_USER))
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Xamsa Média <no-reply@xamsa.sn>')
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # lien valable 24 h
