# -*- coding: utf-8 -*-
"""« Le brief du jour » : synthèse quotidienne de la revue de presse par l'IA.

On rassemble les titres du jour (RevueItem), on demande au LLM une synthèse
structurée, et on l'enregistre (un brief par jour). Robuste : sans clé LLM ou
sans assez d'actualité, on ne génère rien (l'accueil affiche le dernier brief
disponible, ou rien).
"""
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)

PROMPT_BRIEF = (
    "Tu es le rédacteur en chef de Xamsa Media, observatoire de la presse "
    "sénégalaise. À partir des titres de la revue de presse du jour, rédige "
    "« Le brief du jour » : une synthèse claire des principaux sujets de "
    "l'actualité sénégalaise.\n"
    "- Regroupe les titres proches en grands sujets (5 à 7 points maximum).\n"
    "- Chaque point : une phrase courte et informative, sur sa propre ligne, "
    "commençant par un tiret court '- '.\n"
    "- Commence par une phrase d'introduction d'une ligne.\n"
    "- Français correct avec accents. Pas de tiret long (em dash). Pas de "
    "mise en forme markdown (ni **, ni #). N'invente rien qui ne soit pas dans "
    "les titres."
)

MIN_ITEMS = 4


def generer_brief_du_jour(force=False):
    """Génère (ou renvoie) le brief du jour. Retourne l'instance Brief ou None."""
    from veille.models import Brief, RevueItem
    from assistant.llm import LLMIndisponible, texte_libre

    aujourdhui = timezone.localdate()
    existant = Brief.objects.filter(date=aujourdhui).first()
    if existant and not force:
        return existant

    items = list(RevueItem.objects.filter(date__date=aujourdhui)
                 .select_related('source').order_by('-date')[:30])
    if len(items) < MIN_ITEMS:
        return existant  # pas assez d'actualite : on garde l'eventuel brief precedent

    titres = "\n".join('- {} ({})'.format(it.titre_propre, it.source.nom) for it in items)
    try:
        texte = texte_libre(PROMPT_BRIEF, "Titres de la revue de presse du jour :\n" + titres)
    except LLMIndisponible as exc:
        logger.info("Brief non genere (LLM indisponible) : %s", exc)
        return existant

    brief, _ = Brief.objects.update_or_create(date=aujourdhui, defaults={'contenu': texte})
    return brief
