# -*- coding: utf-8 -*-
"""Appel au modele de langage pour rediger la reponse de l'assistant.

Fournisseur par defaut : Google Gemini, via l'API REST (aucune librairie
supplementaire, on reutilise `requests`). L'architecture reste agnostique :
`generer_reponse` s'aiguille selon settings.LLM_PROVIDER.

Toute erreur (cle absente, reseau, quota) leve LLMIndisponible ; l'appelant
retombe alors sur le repli mots-cles.
"""
import logging
import re
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DELAI = 25  # secondes
_STATUTS_A_REESSAYER = {429, 500, 502, 503}


def _post_avec_retry(url, **kwargs):
    """POST avec une nouvelle tentative sur les erreurs transitoires (quota/RPM)."""
    rep = requests.post(url, timeout=DELAI, **kwargs)
    if rep.status_code in _STATUTS_A_REESSAYER:
        time.sleep(1)
        rep = requests.post(url, timeout=DELAI, **kwargs)
    return rep

# Le modele signale les sources vraiment utiles via une ligne finale de ce type.
_MARQUEUR_SOURCES = re.compile(r'\[\[\s*SOURCES?\s*:\s*([0-9,\s]*)\]\]', re.IGNORECASE)

PROMPT_SYSTEME = (
    "Tu es Looy laaj, l'assistant conversationnel de Xamsa Media, un observatoire "
    "independant de la presse et du journalisme senegalais (revue de presse en "
    "direct, enquetes et dossiers, academie de formation au journalisme, espace "
    "communaute). Tu accompagnes les visiteurs du site.\n\n"
    "TON ROLE :\n"
    "- Reponds directement, clairement et de facon satisfaisante, comme un vrai "
    "interlocuteur, en francais.\n"
    "- Tu discutes naturellement : saluer, expliquer ce qu'est Xamsa Media et ce "
    "qu'on peut y faire, orienter l'utilisateur, repondre a des questions "
    "d'actualite, de medias et de journalisme.\n"
    "- Tu restes dans le champ du journalisme, des medias, de l'actualite et de la "
    "societe senegalaise et africaine. Si une question sort completement de ce "
    "champ, reponds brievement et ramene vers ta mission.\n\n"
    "QUALITE DE REPONSE (important) :\n"
    "- Reponds VRAIMENT et precisement a la question posee.\n"
    "- Structure ta reponse : phrases claires et bien construites ; pour une "
    "explication, commence par une phrase de synthese puis developpe.\n"
    "- Va a l'essentiel : en general 2 a 5 phrases. Utilise une courte liste "
    "uniquement si cela aide vraiment la comprehension.\n"
    "- Tiens compte des messages precedents pour garder le fil de la conversation.\n"
    "- Si le CONTEXTE fourni est pertinent, appuie-toi dessus ; sinon reponds de "
    "toi-meme. Si tu ne sais pas, dis-le honnetement plutot que d'inventer.\n"
    "- Ecris un francais correct avec tous les accents. Pas de tiret long (em dash), "
    "utilise des virgules ou des points. Pas de mise en forme markdown (ni **, ni #)."
)

# Consignes specifiques aux 4 intentions de Looy laaj (chatbot / recherche).
_MODES = {
    'rechercher': (
        "\n\nMODE RECHERCHER : l'utilisateur cherche un fait precis (une declaration, "
        "un chiffre, une date). Donne la reponse factuelle directement, en precisant "
        "quand c'est possible qui a dit/fait quoi et a quelle date."),
    'retrouver': (
        "\n\nMODE RETROUVER : l'utilisateur veut retrouver des contenus sur un sujet. "
        "Presente une courte liste des elements pertinents (de quoi il s'agit, et la "
        "periode), du plus recent au plus ancien."),
    'comparer': (
        "\n\nMODE COMPARER : l'utilisateur veut comparer la facon dont plusieurs medias "
        "ou sources traitent un sujet. Organise la reponse source par source et fais "
        "ressortir les points communs et les divergences."),
    'expliquer': (
        "\n\nMODE EXPLIQUER : l'utilisateur veut comprendre un sujet complexe. Explique "
        "simplement, avec des mots accessibles (comme a un adolescent de 15 ans), sans "
        "jargon, en commencant par une phrase de synthese."),
}

# Instruction ajoutee seulement quand on veut afficher des sources (page recherche).
_INSTRUCTION_SOURCES = (
    "\n\nCITATION DES SOURCES :\n"
    "- N'ajoute une source que si elle est vraiment utile pour appuyer ta reponse.\n"
    "- Quand tu utilises des elements du contexte, termine ta reponse par une ligne "
    "isolee au format [[SOURCES: n, n]] listant les numeros utilises. Si aucune "
    "source n'est utile, n'ecris pas cette ligne."
)


class LLMIndisponible(Exception):
    """Le LLM n'a pas pu produire de reponse (cle manquante, erreur reseau...)."""


def _bloc_contexte(documents):
    if not documents:
        return "(aucun contexte : reponds de toi-meme, sans source)"
    lignes = []
    for i, d in enumerate(documents, 1):
        extrait = d.get('extrait') or ''
        lignes.append(
            "[{n}] {titre}\n    Source : {origine} ({type})\n    Extrait : {extrait}".format(
                n=i, titre=d.get('titre', ''), origine=d.get('origine', ''),
                type=d.get('type', ''), extrait=extrait)
        )
    return "\n".join(lignes)


def _extraire_sources(texte, nb_documents):
    """Separe le texte affichable des indices de sources cites par le modele.

    Retourne (texte_propre, [indices 0-based valides]).
    """
    indices = []
    for correspondance in _MARQUEUR_SOURCES.finditer(texte):
        for morceau in correspondance.group(1).split(','):
            morceau = morceau.strip()
            if morceau.isdigit():
                i = int(morceau) - 1
                if 0 <= i < nb_documents and i not in indices:
                    indices.append(i)
    texte_propre = _MARQUEUR_SOURCES.sub('', texte).strip()
    return texte_propre, indices


def texte_libre(prompt_systeme, message, max_tokens=900):
    """Appel LLM generique (prompt systeme + message). Retourne le texte.

    Utilise par le « brief du jour ». Leve LLMIndisponible en cas d'echec.
    """
    provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
    if provider == 'gemini':
        return _gemini_texte(prompt_systeme, message, max_tokens)
    if provider == 'groq':
        return _groq_texte(prompt_systeme, message, max_tokens)
    raise LLMIndisponible("Fournisseur LLM inconnu : {}".format(provider))


def _gemini_texte(prompt_systeme, message, max_tokens):
    cle = getattr(settings, 'GEMINI_API_KEY', '')
    if not cle:
        raise LLMIndisponible("GEMINI_API_KEY absente.")
    modele = getattr(settings, 'GEMINI_MODEL', 'gemini-flash-lite-latest')
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "{modele}:generateContent".format(modele=modele))
    charge = {
        "system_instruction": {"parts": [{"text": prompt_systeme}]},
        "contents": [{"role": "user", "parts": [{"text": message}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": max_tokens},
    }
    try:
        rep = _post_avec_retry(url, params={"key": cle}, json=charge)
    except requests.RequestException as exc:
        raise LLMIndisponible("Erreur reseau Gemini : {}".format(exc))
    if rep.status_code != 200:
        raise LLMIndisponible("Gemini a repondu {} : {}".format(rep.status_code, rep.text[:200]))
    try:
        parts = rep.json()['candidates'][0]['content']['parts']
        texte = ''.join(p.get('text', '') for p in parts).strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMIndisponible("Reponse Gemini inattendue : {}".format(exc))
    if not texte:
        raise LLMIndisponible("Gemini a renvoye une reponse vide.")
    return texte


def _groq_texte(prompt_systeme, message, max_tokens):
    cle = getattr(settings, 'GROQ_API_KEY', '')
    if not cle:
        raise LLMIndisponible("GROQ_API_KEY absente.")
    modele = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
    charge = {
        "model": modele,
        "messages": [{"role": "system", "content": prompt_systeme},
                     {"role": "user", "content": message}],
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }
    try:
        rep = _post_avec_retry("https://api.groq.com/openai/v1/chat/completions",
                               headers={"Authorization": "Bearer {}".format(cle)}, json=charge)
    except requests.RequestException as exc:
        raise LLMIndisponible("Erreur reseau Groq : {}".format(exc))
    if rep.status_code != 200:
        raise LLMIndisponible("Groq a repondu {} : {}".format(rep.status_code, rep.text[:200]))
    try:
        texte = rep.json()['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMIndisponible("Reponse Groq inattendue : {}".format(exc))
    if not texte:
        raise LLMIndisponible("Groq a renvoye une reponse vide.")
    return texte


def _prompt_systeme(avec_sources, mode=None):
    prompt = PROMPT_SYSTEME + _MODES.get(mode or '', '')
    return prompt + (_INSTRUCTION_SOURCES if avec_sources else '')


def generer_reponse(question, documents, historique=None, avec_sources=True, mode=None):
    """Retourne (texte, indices_sources). Leve LLMIndisponible en cas d'echec.

    Si avec_sources est faux, aucune source n'est renvoyee et les eventuels
    marqueurs [[SOURCES]] sont retires du texte (mode chatbot : texte seul).
    `mode` (rechercher/retrouver/comparer/expliquer) adapte les consignes.
    """
    prompt = _prompt_systeme(avec_sources, mode)
    provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
    if provider == 'gemini':
        texte = _gemini(question, documents, historique, prompt)
    elif provider == 'groq':
        texte = _groq(question, documents, historique, prompt)
    else:
        raise LLMIndisponible("Fournisseur LLM inconnu : {}".format(provider))
    if not avec_sources:
        return _MARQUEUR_SOURCES.sub('', texte).strip(), []
    return _extraire_sources(texte, len(documents))


def _messages_openai(question, documents, historique, prompt_systeme):
    """Construit une liste de messages au format OpenAI/Groq."""
    messages = [{"role": "system", "content": prompt_systeme}]
    for tour in (historique or [])[-6:]:
        role = 'user' if tour.get('role') == 'user' else 'assistant'
        messages.append({"role": role, "content": tour.get('texte', '')})
    messages.append({"role": "user", "content": (
        "CONTEXTE (numerote) :\n{contexte}\n\nQUESTION :\n{question}".format(
            contexte=_bloc_contexte(documents), question=question))})
    return messages


def _groq(question, documents, historique, prompt_systeme):
    cle = getattr(settings, 'GROQ_API_KEY', '')
    if not cle:
        raise LLMIndisponible("GROQ_API_KEY absente.")
    modele = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
    charge = {
        "model": modele,
        "messages": _messages_openai(question, documents, historique, prompt_systeme),
        "temperature": 0.35,
        "max_tokens": 600,
    }
    try:
        rep = _post_avec_retry(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": "Bearer {}".format(cle)}, json=charge)
    except requests.RequestException as exc:
        raise LLMIndisponible("Erreur reseau Groq : {}".format(exc))
    if rep.status_code != 200:
        raise LLMIndisponible("Groq a repondu {} : {}".format(rep.status_code, rep.text[:200]))
    try:
        texte = rep.json()['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMIndisponible("Reponse Groq inattendue : {}".format(exc))
    if not texte:
        raise LLMIndisponible("Groq a renvoye une reponse vide.")
    return texte


def _gemini(question, documents, historique, prompt_systeme):
    cle = getattr(settings, 'GEMINI_API_KEY', '')
    if not cle:
        raise LLMIndisponible("GEMINI_API_KEY absente.")

    modele = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "{modele}:generateContent".format(modele=modele))

    contents = []
    for tour in (historique or [])[-6:]:  # derniers echanges pour garder le fil
        role = 'user' if tour.get('role') == 'user' else 'model'
        contents.append({"role": role, "parts": [{"text": tour.get('texte', '')}]})

    message = (
        "CONTEXTE (numerote) :\n{contexte}\n\n"
        "QUESTION :\n{question}"
    ).format(contexte=_bloc_contexte(documents), question=question)
    contents.append({"role": "user", "parts": [{"text": message}]})

    charge = {
        "system_instruction": {"parts": [{"text": prompt_systeme}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": 600},
    }

    try:
        rep = _post_avec_retry(url, params={"key": cle}, json=charge)
    except requests.RequestException as exc:
        raise LLMIndisponible("Erreur reseau Gemini : {}".format(exc))

    if rep.status_code != 200:
        raise LLMIndisponible("Gemini a repondu {} : {}".format(
            rep.status_code, rep.text[:200]))

    try:
        data = rep.json()
        parts = data['candidates'][0]['content']['parts']
        texte = ''.join(p.get('text', '') for p in parts).strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMIndisponible("Reponse Gemini inattendue : {}".format(exc))

    if not texte:
        raise LLMIndisponible("Gemini a renvoye une reponse vide.")
    return texte
