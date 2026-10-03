# -*- coding: utf-8 -*-
"""Filtres de gabarit Xamsa : temps écoulé depuis la publication, en français."""
from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def publie_depuis(value):
    """« il y a 2 h », « il y a 3 jours »… à partir d'une date de publication.

    < 1 min : à l'instant ; < 1 h : minutes ; < 24 h : heures ; < 7 j : jours ;
    < 1 mois : semaines ; < 1 an : mois ; au-delà : années.
    """
    if not value:
        return ''
    maintenant = timezone.now()
    try:
        secondes = int((maintenant - value).total_seconds())
    except TypeError:
        return ''
    if secondes < 0:
        secondes = 0
    if secondes < 60:
        return "à l'instant"
    minutes = secondes // 60
    if minutes < 60:
        return "il y a {} min".format(minutes)
    heures = minutes // 60
    if heures < 24:
        return "il y a {} h".format(heures)
    jours = heures // 24
    if jours < 7:
        return "il y a {} jour{}".format(jours, 's' if jours > 1 else '')
    if jours < 30:
        semaines = jours // 7
        return "il y a {} semaine{}".format(semaines, 's' if semaines > 1 else '')
    if jours < 365:
        mois = jours // 30
        return "il y a {} mois".format(mois)
    annees = jours // 365
    return "il y a {} an{}".format(annees, 's' if annees > 1 else '')
