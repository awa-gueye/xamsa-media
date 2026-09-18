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


class Bibliotheque(models.Model):
    """Bibliothèque interne : l'ensemble des productions de Xamsa Média
    (documentaires, enquêtes, documents, vidéos...). Visible uniquement par
    l'administrateur, jamais par les utilisateurs."""
    TYPES = [
        ('documentaire', 'Documentaire'),
        ('enquete', 'Enquête'),
        ('reportage', 'Reportage'),
        ('document', 'Document'),
        ('rapport', 'Rapport'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
        ('photo', 'Photo / Album'),
        ('autre', 'Autre'),
    ]
    titre = models.CharField(max_length=240)
    type = models.CharField(max_length=20, choices=TYPES, default='document')
    description = models.TextField(blank=True)
    image = models.ImageField('Vignette', upload_to='bibliotheque/images/', blank=True, null=True)
    fichier = models.FileField('Fichier (PDF, vidéo, audio, document...)',
                               upload_to='bibliotheque/fichiers/', blank=True, null=True)
    lien = models.URLField('Lien externe', max_length=600, blank=True)
    video_url = models.URLField('Vidéo YouTube', max_length=600, blank=True)
    date = models.DateTimeField('Date', default=timezone.now)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Document de la bibliothèque'
        verbose_name_plural = 'Bibliothèque (productions Xamsa)'

    @property
    def visuel(self):
        return self.image.url if self.image else ''

    @property
    def video_embed(self):
        from core.media_embed import youtube_embed
        return youtube_embed(self.video_url)

    def __str__(self):
        return self.titre
