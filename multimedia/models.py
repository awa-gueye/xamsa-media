# -*- coding: utf-8 -*-
"""Contenus multimedia : documentaires et podcasts."""
from django.db import models
from django.utils import timezone


class Media(models.Model):
    DOCUMENTAIRE = 'documentaire'
    PODCAST = 'podcast'
    TYPES = [(DOCUMENTAIRE, 'Documentaire'), (PODCAST, 'Podcast')]

    titre = models.CharField(max_length=220)
    type = models.CharField(max_length=20, choices=TYPES, default=DOCUMENTAIRE)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='media/', blank=True, null=True)
    image_url = models.URLField(max_length=600, blank=True)
    lien = models.URLField('Lien (video/audio)', max_length=600, blank=True)
    duree = models.CharField('Duree', max_length=30, blank=True)
    publie = models.BooleanField(default=True)
    date_publication = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date_publication']
        verbose_name = 'Media'
        verbose_name_plural = 'Medias'

    @property
    def visuel(self):
        if self.image:
            return self.image.url
        return self.image_url

    def __str__(self):
        return self.titre
