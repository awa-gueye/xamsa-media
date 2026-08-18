# -*- coding: utf-8 -*-
"""Recherche web pour les sources externes (DuckDuckGo, sans cle API).

Encapsule la librairie ddgs. Si elle est absente ou si la recherche echoue, on
renvoie une liste vide : l'assistant continue de fonctionner avec le seul
contenu du site.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


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
        if not url:
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
