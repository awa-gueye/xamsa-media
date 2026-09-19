# -*- coding: utf-8 -*-
"""Couches de sécurité applicatives : en-têtes (CSP, Permissions-Policy) et
limitation de débit (anti-brute-force et anti-scraping).

Défense en profondeur : ces protections s'ajoutent à Cloudflare (WAF/anti-bot en
amont) et aux réglages Django (HTTPS, HSTS, cookies sécurisés). Aucune mesure
n'est infaillible à 100 %, mais l'empilement rend l'abus coûteux et lent.
"""
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse

# ---------------------------------------------------------------------------
# IP réelle du client, même derrière Cloudflare / le proxy de Render.
# ---------------------------------------------------------------------------
def client_ip(request):
    for entete in ('HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'):
        val = request.META.get(entete)
        if val:
            return val.split(',')[0].strip()
    return '0.0.0.0'


# ---------------------------------------------------------------------------
# En-têtes de sécurité (CSP + Permissions-Policy + divers).
# ---------------------------------------------------------------------------
# Politique de sécurité du contenu. img/media/frame larges car le mur de la
# presse et les articles affichent des images/vidéos de domaines variés.
_CSP = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "img-src 'self' data: blob: https:; "
    "media-src 'self' https:; "
    "font-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self' 'unsafe-inline'; "
    "connect-src 'self' https:; "
    "worker-src 'self'; "
    "manifest-src 'self'; "
    "frame-src https://www.youtube.com https://www.youtube-nocookie.com; "
    "upgrade-insecure-requests"
)

_PERMISSIONS = ("geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
                "magnetometer=(), gyroscope=(), interest-cohort=()")


class SecurityHeadersMiddleware:
    """Ajoute les en-têtes de sécurité modernes non fournis par Django."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Content-Security-Policy', _CSP)
        response.setdefault('Permissions-Policy', _PERMISSIONS)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
        return response


# ---------------------------------------------------------------------------
# Limitation de débit (rate limiting) par IP.
# ---------------------------------------------------------------------------
# (préfixe de chemin, méthode ou None, nombre max, fenêtre en secondes).
# L'anti-brute-force protège l'authentification ; l'anti-scraping plafonne le
# débit global de lecture.
# Seuils volontairement généreux : au Sénégal beaucoup d'utilisateurs partagent
# une même IP (NAT opérateur mobile). Ces valeurs bloquent l'abus automatisé
# (des centaines/milliers de requêtes) sans gêner des humains partageant une IP.
_REGLES = [
    ('/connexion/', 'POST', 25, 300),
    ('/inscription/', 'POST', 15, 600),
    ('/mot-de-passe/', 'POST', 10, 600),
    ('/assistant/ask/', 'POST', 45, 60),
    ('/newsletter/', 'POST', 10, 600),
    ('/publier/', 'POST', 25, 3600),
]

# Plafond global (anti-scraping) : requêtes dynamiques par IP et par minute.
_GLOBAL_MAX = 300
_GLOBAL_WINDOW = 60

# Chemins jamais limités (fichiers statiques/medias servis par WhiteNoise, PWA).
_EXCLUS = ('/static/', '/media/', '/sw.js', '/manifest.json', '/favicon.ico')


def _depasse(scope, ip, limite, fenetre):
    """Compteur à fenêtre fixe : True si la limite est dépassée pour cette IP."""
    cle = 'rl:{}:{}'.format(scope, ip)
    if cache.add(cle, 1, fenetre):   # première requête de la fenêtre
        return False
    try:
        n = cache.incr(cle)
    except ValueError:               # la clé a expiré entre-temps
        cache.add(cle, 1, fenetre)
        return False
    return n > limite


class RateLimitMiddleware:
    """Bloque (429) les IP qui dépassent les seuils. Désactivable via
    SECURITY_RATELIMIT=False (settings)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.actif = getattr(settings, 'SECURITY_RATELIMIT', True)

    def __call__(self, request):
        if not self.actif:
            return self.get_response(request)
        chemin = request.path
        if not chemin.startswith(_EXCLUS):
            ip = client_ip(request)
            # 1) Règles ciblées (auth, assistant...).
            for prefixe, methode, limite, fenetre in _REGLES:
                if chemin.startswith(prefixe) and (methode is None or request.method == methode):
                    if _depasse(prefixe + (methode or ''), ip, limite, fenetre):
                        return self._refus(request, fenetre)
            # 2) Plafond global anti-scraping.
            if _depasse('global', ip, _GLOBAL_MAX, _GLOBAL_WINDOW):
                return self._refus(request, _GLOBAL_WINDOW)
        return self.get_response(request)

    def _refus(self, request, retry):
        msg = "Trop de requêtes. Réessayez dans un moment."
        if request.path.startswith('/assistant/') or request.headers.get('x-requested-with'):
            resp = JsonResponse({'texte': msg, 'sources': []}, status=429)
        else:
            resp = HttpResponse(msg, status=429, content_type='text/plain; charset=utf-8')
        resp['Retry-After'] = str(retry)
        return resp
