# -*- coding: utf-8 -*-
"""Moteur de l'assistant Looy laaj (partage entre le chatbot et la recherche).

Enchaine : classification du message -> recuperation de contexte (contenu du
site + web, seulement si utile) -> redaction par le LLM -> selection des sources
reellement citees. Repli robuste sans cle API ou en cas d'erreur.
"""
import logging
import unicodedata
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from django.conf import settings

from .llm import LLMIndisponible, generer_reponse
from .retrieval import documents_du_site
from .web_search import documents_du_web

logger = logging.getLogger(__name__)

# Messages "sociaux" (salutations, remerciements, bavardage) : pas de recherche,
# le LLM repond de lui-meme.
_SALUTATIONS = {
    'bonjour', 'bonsoir', 'salut', 'coucou', 'hello', 'hi', 'hey', 'yo', 'slt',
    'cc', 'merci', 'bye', 'ok', 'daccord', 'salamalekoum', 'asalamalekoum',
    'nangadef', 'jamm', 'bjr',
}
_PHRASES_SOCIALES = (
    'ca va', 'comment vas tu', 'comment allez vous', 'qui es tu', 'tu es qui',
    'que fais tu', 'tu fais quoi', 'au revoir', 'a bientot', 'bonne journee',
    'merci beaucoup', 'comment ca va',
)


def _normaliser(texte):
    texte = unicodedata.normalize('NFD', texte.lower())
    texte = ''.join(c for c in texte if unicodedata.category(c) != 'Mn')
    return ''.join(c if c.isalnum() or c.isspace() else ' ' for c in texte).split()


def est_social(question):
    """Vrai si le message est une salutation / du bavardage (pas une vraie question)."""
    mots = _normaliser(question)
    if not mots:
        return True
    if len(mots) <= 4 and any(m in _SALUTATIONS for m in mots):
        return True
    aplat = ' '.join(mots)
    return any(p in aplat for p in _PHRASES_SOCIALES)


def _sources_depuis(documents, indices=None, limite=5):
    """Met en forme les sources pour le front. Si indices est fourni, on ne garde
    que celles-la ; sinon toutes (deduplication par URL)."""
    choisis = [documents[i] for i in indices] if indices is not None else documents
    vues, sources = set(), []
    for d in choisis:
        url = d.get('url')
        if not url or url in vues:
            continue
        vues.add(url)
        sources.append({'titre': d.get('titre', ''), 'origine': d.get('origine', ''),
                        'url': url})
        if len(sources) >= limite:
            break
    return sources


def _repli(question, documents):
    """Reponse sans LLM. Pour un message social, on discute simplement ; sinon on
    oriente vers les elements trouves (sans noyer l'utilisateur de liens)."""
    if est_social(question) or not documents:
        return {
            'texte': ("Bonjour, je suis Looy laaj, l'assistant de Xamsa Media. "
                      "Je peux vous aider a suivre l'actualite de la presse "
                      "senegalaise, retrouver un sujet, comprendre le paysage "
                      "mediatique ou vous orienter sur le site. Que cherchez-vous ?"),
            'sources': [],
        }
    return {
        'texte': ("Voici ce que j'ai trouve de plus proche dans notre base et sur "
                  "le web. Le service de redaction automatique est momentanement "
                  "indisponible."),
        'sources': _sources_depuis(documents, limite=4),
    }


def _rassembler_contexte(question, avec_web=True):
    """Recupere contenu du site + web en parallele, avec un plafond de temps sur
    la recherche web (la plus lente) : au-dela, on repond sans elle."""
    web_actif = avec_web and getattr(settings, 'WEB_SEARCH_ENABLED', True)
    timeout_web = getattr(settings, 'ASSISTANT_WEB_TIMEOUT', 5) + 1  # marge > timeout reseau

    with ThreadPoolExecutor(max_workers=2) as ex:
        futur_site = ex.submit(documents_du_site, question)
        futur_web = ex.submit(documents_du_web, question) if web_actif else None

        documents = []
        try:
            documents += futur_site.result(timeout=6)
        except Exception as exc:
            logger.warning("Retrieval site en echec : %s", exc)
        if futur_web is not None:
            try:
                documents += futur_web.result(timeout=timeout_web)
            except FuturesTimeout:
                logger.info("Recherche web trop lente : reponse sans sources web.")
            except Exception as exc:
                logger.warning("Recherche web en echec : %s", exc)
    return documents


def repondre(question, historique=None, max_sources=5, avec_web=True, avec_sources=True):
    """Point d'entree unique. Retourne {'texte': str, 'sources': [...]}.

    - Mode chatbot : avec_web=False, avec_sources=False (texte clair, aucun lien).
    - Mode recherche : avec_web=True, avec_sources=True (facon moteur de reponse).
    """
    question = (question or '').strip()
    if not question:
        return {'texte': "Posez-moi une question.", 'sources': []}

    # 1. Contexte seulement pour les vraies questions (pas pour les salutations).
    documents = []
    if not est_social(question):
        documents = _rassembler_contexte(question, avec_web=avec_web)

    # 2. Redaction par le LLM.
    try:
        texte, indices = generer_reponse(question, documents, historique=historique,
                                         avec_sources=avec_sources)
        sources = _sources_depuis(documents, indices=indices, limite=max_sources) if avec_sources else []
        return {'texte': texte, 'sources': sources}
    except LLMIndisponible as exc:
        logger.info("Repli (LLM indisponible) : %s", exc)
        if not avec_sources:  # mode chatbot : texte clair, jamais de liens.
            if est_social(question):
                return {'texte': ("Bonjour, je suis Looy laaj, l'assistant de Xamsa "
                                  "Media. Comment puis-je vous aider ?"), 'sources': []}
            return {'texte': ("Je ne parviens pas a repondre a l'instant. Veuillez "
                              "reessayer dans un moment."), 'sources': []}
        return _repli(question, documents)
