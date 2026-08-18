# -*- coding: utf-8 -*-
"""Recuperation du contexte a partir du contenu de Xamsa Media (RAG local).

On selectionne les articles editoriaux et les items de revue de presse les plus
pertinents pour la question, et on les met en forme en "documents" reutilisables
par le LLM comme par le repli mots-cles.
"""
from django.conf import settings
from django.db.models import Q

from redaction.models import Article
from veille.models import RevueItem
from veille.text_utils import nettoyer_texte

MOTS_VIDES = {
    'dans', 'pour', 'avec', 'les', 'des', 'une', 'que', 'qui', 'sur', 'est',
    'aux', 'par', 'plus', 'the', 'and', 'quoi', 'comment', 'quel', 'quelle',
    'quels', 'quelles', 'pourquoi', 'combien', 'sont', 'cette', 'entre',
    'vous', 'nous', 'ton', 'son', 'ses', 'mes', 'leur', 'leurs',
}


def mots_cles(question):
    """Extrait les mots significatifs (plus de 3 lettres, hors mots vides)."""
    nettoye = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in question.lower())
    return [m for m in nettoye.split() if len(m) > 3 and m not in MOTS_VIDES]


def _tronquer(texte, limite=320):
    texte = (texte or '').strip()
    return texte if len(texte) <= limite else texte[:limite].rsplit(' ', 1)[0] + '...'


def documents_du_site(question, max_resultats=None):
    """Retourne une liste de documents pertinents du site.

    Chaque document : {titre, extrait, origine, url, type}. Si la question ne
    contient pas de mot-cle exploitable, on renvoie les contenus les plus recents
    pour rester utile ("actualite du jour").
    """
    if max_resultats is None:
        max_resultats = getattr(settings, 'ASSISTANT_MAX_SITE_RESULTS', 5)

    mots = mots_cles(question)
    articles_qs = Article.objects.filter(publie=True).select_related('categorie')
    items_qs = RevueItem.objects.select_related('source')

    if mots:
        filtre_art = Q()
        filtre_rev = Q()
        for mot in mots:
            filtre_art |= Q(titre__icontains=mot) | Q(chapo__icontains=mot) | Q(corps__icontains=mot)
            filtre_rev |= Q(titre__icontains=mot) | Q(resume__icontains=mot)
        articles_qs = articles_qs.filter(filtre_art)
        items_qs = items_qs.filter(filtre_rev)

    part_articles = max(1, max_resultats // 2)
    articles = list(articles_qs[:part_articles])
    items = list(items_qs[:max_resultats - len(articles)])

    documents = []
    for a in articles:
        documents.append({
            'titre': a.titre,
            'extrait': _tronquer(a.chapo or a.corps),
            'origine': 'Xamsa Media',
            'url': a.get_absolute_url(),
            'type': 'article',
        })
    for it in items:
        documents.append({
            'titre': it.titre_propre,
            'extrait': _tronquer(nettoyer_texte(it.resume)),
            'origine': it.source.nom,
            'url': it.url,
            'type': 'revue',
        })
    return documents
