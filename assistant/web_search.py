# -*- coding: utf-8 -*-
"""Recherche web pour les sources externes (DuckDuckGo, sans cle API).

Encapsule la librairie ddgs. Si elle est absente ou si la recherche echoue, on
renvoie une liste vide : l'assistant continue de fonctionner avec le seul
contenu du site.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Liste blanche STRICTE des domaines autorisés : aucune information provenant
# d'un autre site ne doit apparaître (ni dans la recherche, ni dans Looy laaj).
DOMAINES_AUTORISES = {
    'seneweb.com', 'leral.net', 'rts.sn', 'lesoleil.sn', 'aps.sn', 'dakaractu.com',
    'lequotidien.sn', 'liberationonline.sn', 'igfm.sn', 'igfm.com', 'sudquotidien.sn',
    'lenquete.sn', 'lamaisondesreporters.com', 'africacheck.org', 'wiwsport.com',
    'dsports.sn', 'footafrica.com', 'footnewsafrica.com', 'lsfp.sn', 'galsenfoot.com',
    'fsfoot.sn', 'lesjecos.com', 'financialafrik.com', 'ola.sn',
}


def domaine_autorise(url):
    """Vrai si l'URL provient d'un des sites autorisés (ou d'un ministère .gouv.sn)."""
    from urllib.parse import urlparse
    try:
        hote = (urlparse(url).netloc or '').lower().split(':')[0]
    except Exception:
        return False
    if hote.startswith('www.'):
        hote = hote[4:]
    if hote.endswith('.gouv.sn') or hote == 'gouv.sn':   # sites des ministères
        return True
    return any(hote == d or hote.endswith('.' + d) for d in DOMAINES_AUTORISES)


def documents_du_web(question, max_resultats=None):
    """Retourne une liste de documents web : {titre, extrait, origine, url, type}."""
    if not getattr(settings, 'WEB_SEARCH_ENABLED', True):
        return []
    if max_resultats is None:
        max_resultats = getattr(settings, 'ASSISTANT_MAX_WEB_RESULTS', 4)

    try:
        from ddgs import DDGS
    except ImportError:
        logger.info("ddgs non installe : recherche web desactivee.")
        return []

    backend = getattr(settings, 'ASSISTANT_WEB_BACKEND', 'duckduckgo')
    delai = getattr(settings, 'ASSISTANT_WEB_TIMEOUT', 5)
    # Backends essayes dans l'ordre : on s'arrete au premier qui renvoie des resultats.
    backends = [b.strip() for b in backend.split(',') if b.strip()] or ['duckduckgo']

    resultats = []
    for b in backends:
        try:
            resultats = list(DDGS(timeout=delai).text(
                question, region='fr-fr', safesearch='moderate',
                backend=b, max_results=max_resultats) or [])
            if resultats:
                break
        except Exception as exc:  # reseau, quota, aucun resultat : on tente le suivant.
            logger.info("Recherche web (%s) indisponible : %s", b, exc)

    documents = []
    for r in resultats:
        url = r.get('href') or r.get('url') or ''
        if not url or not domaine_autorise(url):   # aucun site hors liste blanche
            continue
        documents.append({
            'titre': (r.get('title') or url).strip(),
            'extrait': (r.get('body') or '').strip(),
            'origine': _domaine(url),
            'url': url,
            'type': 'web',
        })
    return documents


def _domaine(url):
    try:
        from urllib.parse import urlparse
        hote = urlparse(url).netloc
        return hote[4:] if hote.startswith('www.') else hote
    except Exception:
        return 'Web'
