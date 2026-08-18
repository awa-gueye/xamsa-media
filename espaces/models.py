# -*- coding: utf-8 -*-
"""Contenus des espaces Academie, Communaute et Medias du Senegal.

Trois modeles souples : un champ `type` filtre chaque sous-onglet.
"""
from django.db import models
from django.utils import timezone


class _Base(models.Model):
    titre = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=600, blank=True)
    logo = models.ImageField('Logo (fichier)', upload_to='logos/', blank=True, null=True)
    lien = models.URLField(max_length=600, blank=True)
    meta = models.CharField('Info complémentaire', max_length=140, blank=True)
    publie = models.BooleanField(default=True)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
        ordering = ['-date']

    def __str__(self):
        return self.titre

    @property
    def initiales(self):
        """Monogramme affiche a defaut de logo (ex. 'RTS1', 'WT' pour Walf TV)."""
        import re
        premier = re.split(r'[\s(]', self.titre.strip())[0]
        premier = re.sub(r'[^0-9A-Za-zÀ-ÿ]', '', premier)
        if len(premier) >= 2:
            return premier[:4].upper()
        mots = [re.sub(r'[^0-9A-Za-zÀ-ÿ]', '', m) for m in self.titre.split()]
        return ''.join(m[0] for m in mots if m)[:3].upper() or '?'


class Ressource(_Base):
    """Academie : cours, formations, webinaires, ressources, certifications."""
    TYPES = [('cours', 'Cours'), ('formation', 'Formation'), ('webinaire', 'Webinaire'),
             ('ressource', 'Ressource'), ('certification', 'Certification')]
    type = models.CharField(max_length=20, choices=TYPES, default='cours')


class ItemCommunaute(_Base):
    """Communaute : contribution, concours, association, opportunite."""
    TYPES = [('contribution', 'Espace contribution'), ('concours', 'Concours'),
             ('association', 'Association de presse'), ('opportunite', 'Opportunité')]
    type = models.CharField(max_length=20, choices=TYPES, default='contribution')


class MediaSenegal(_Base):
    """Medias du Senegal : histoire, portraits, TV, radios, presse, numerique, podcasts."""
    TYPES = [('histoire', 'Histoire des médias'), ('portrait', 'Portrait de journaliste'),
             ('tv', 'Chaîne TV'), ('radio', 'Radio'), ('presse', 'Presse écrite'),
             ('numerique', 'Média numérique'), ('podcast', 'Podcast')]
    type = models.CharField(max_length=20, choices=TYPES, default='histoire')
