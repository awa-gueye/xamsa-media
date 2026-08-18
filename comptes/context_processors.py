# -*- coding: utf-8 -*-
"""Contextes globaux : notifications non lues + suggestions du chatbot."""
import re


def notifications(request):
    ctx = {'notifs_non_lues': 0, 'moderation_en_attente': 0}
    if request.user.is_authenticated:
        ctx['notifs_non_lues'] = request.user.notifications.filter(lu=False).count()
        if request.user.is_superuser:
            from .models import Contribution
            ctx['moderation_en_attente'] = Contribution.objects.filter(statut='attente').count()
    return ctx


def chatbot_suggestions(request):
    """Puces du chatbot dérivées des sujets de l'actualité récente (revue de presse)."""
    from veille.models import RevueItem
    vus, sugg = set(), []
    try:
        for it in RevueItem.objects.select_related('source').order_by('-date')[:15]:
            # Le sujet = ce qui precede le premier separateur (:, tiret long, |).
            sujet = re.split(r'[:–—|]', it.titre_propre, 1)[0].strip()
            mots = sujet.split()
            if len(mots) > 6:
                sujet = ' '.join(mots[:6])
            cle = sujet.lower()
            if len(sujet) < 10 or cle in vus:
                continue
            vus.add(cle)
            sugg.append(sujet)
            if len(sugg) >= 4:
                break
    except Exception:
        return {'chatbot_suggestions': []}
    return {'chatbot_suggestions': sugg}
