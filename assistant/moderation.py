# -*- coding: utf-8 -*-
"""Pré-modération des contributions par l'IA (Looy laaj).

L'IA évalue une contribution soumise et rend un verdict (publier / reviser /
rejeter), un score de confiance (0-100) et une courte justification. L'appelant
décide ensuite quoi en faire (publication auto, rejet auto, ou file humaine).

Robuste : sans clé LLM ou en cas d'erreur, retourne None -> file humaine normale.
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

PROMPT_MODERATION = (
    "Tu es modérateur pour Xamsa Media, observatoire de la presse et du "
    "journalisme sénégalais. On te soumet une contribution d'un utilisateur. "
    "Évalue-la selon ces critères :\n"
    "- Pertinence : en lien avec le journalisme, les médias, l'actualité ou la "
    "société sénégalaise/africaine.\n"
    "- Qualité : contenu réel, cohérent, compréhensible, pas vide ni bâclé.\n"
    "- Sécurité : PAS de spam, publicité, arnaque, propos haineux, violents, "
    "diffamatoires, à caractère sexuel ou illégaux.\n\n"
    "Réponds UNIQUEMENT par un objet JSON strict, sans texte autour, de la forme :\n"
    '{"decision": "publier|reviser|rejeter", "score": <entier 0-100>, "raison": "<courte phrase>"}\n'
    "- \"publier\" : clairement pertinent, de qualité et sûr.\n"
    "- \"reviser\" : acceptable mais douteux, hors sujet partiel, incomplet, à "
    "vérifier par un humain.\n"
    "- \"rejeter\" : spam, abus, dangereux ou totalement hors sujet.\n"
    "- score = ta confiance dans la qualité ET la sûreté du contenu (100 = "
    "excellent et sûr, 0 = à rejeter).\n"
    "- raison = une phrase courte en français expliquant ta décision."
)

_JSON = re.compile(r'\{.*\}', re.DOTALL)


def evaluer_contribution(contrib):
    """Retourne {'decision','score','raison'} ou None si indisponible."""
    from assistant.llm import LLMIndisponible, texte_libre

    corps = re.sub(r'<[^>]+>', ' ', contrib.corps or '')
    contenu = (
        "TYPE : {type}\nTITRE : {titre}\nRESUME : {resume}\nCONTENU : {corps}"
    ).format(type=contrib.get_type_display(), titre=contrib.titre,
             resume=contrib.resume or '(aucun)', corps=corps[:4000] or '(vide)')

    try:
        reponse = texte_libre(PROMPT_MODERATION, contenu, max_tokens=200)
    except LLMIndisponible as exc:
        logger.info("Moderation IA indisponible : %s", exc)
        return None

    correspondance = _JSON.search(reponse or '')
    if not correspondance:
        logger.info("Moderation : reponse non-JSON : %s", (reponse or '')[:120])
        return None
    try:
        data = json.loads(correspondance.group(0))
    except ValueError:
        return None

    decision = str(data.get('decision', '')).lower().strip()
    if decision not in ('publier', 'reviser', 'rejeter'):
        return None
    try:
        score = max(0, min(100, int(data.get('score', 0))))
    except (TypeError, ValueError):
        score = 0
    raison = str(data.get('raison', ''))[:300]
    return {'decision': decision, 'score': score, 'raison': raison}


# Seuils de publication automatique (mode semi-automatique).
SEUIL_CONFIANCE = 70   # contributeur "de confiance" : verdict publier suffit au-dela
SEUIL_STANDARD = 85    # utilisateur normal : exigence plus haute


def appliquer_moderation(contrib, de_confiance=False):
    """Évalue la contribution et met à jour son statut (semi-automatique).

    - rejeter                -> statut 'refuse'
    - publier + score assez haut (seuil abaissé si de_confiance) -> 'publie'
    - sinon                  -> reste 'attente' (file humaine), verdict enregistré
    Retourne le verdict (dict) ou None.
    """
    verdict = evaluer_contribution(contrib)
    if not verdict:
        contrib.moderation_verdict = ''
        contrib.moderation_note = ''
        contrib.save(update_fields=['moderation_verdict', 'moderation_note'])
        return None

    contrib.moderation_verdict = verdict['decision']
    contrib.moderation_score = verdict['score']
    contrib.moderation_note = verdict['raison']

    seuil = SEUIL_CONFIANCE if de_confiance else SEUIL_STANDARD
    if verdict['decision'] == 'rejeter':
        contrib.statut = 'refuse'
    elif verdict['decision'] == 'publier' and verdict['score'] >= seuil:
        contrib.statut = 'publie'
    else:
        contrib.statut = 'attente'

    contrib.save(update_fields=['moderation_verdict', 'moderation_score',
                                'moderation_note', 'statut'])
    return verdict
