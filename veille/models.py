# -*- coding: utf-8 -*-
"""Sources de presse suivies et items agreges (revue de presse)."""
from django.db import models

from veille.text_utils import nettoyer_texte


class Source(models.Model):
    nom = models.CharField(max_length=120, unique=True)
    url_rss = models.URLField('Flux RSS', max_length=500)
    site = models.URLField('Site web', max_length=300, blank=True)
    categorie = models.CharField(max_length=60, default='Presse')
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class RevueItem(models.Model):
    """Titre + resume + image + lien vers l'original (jamais le texte integral)."""
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='items')
    titre = models.CharField(max_length=400)
    resume = models.TextField('Resume / analyse', blank=True)
    url = models.URLField('Lien vers la source', max_length=600)
    image_url = models.URLField('Image (URL)', max_length=600, blank=True)
    date = models.DateTimeField()

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(fields=['source', 'url'], name='revueitem_unique_source_url'),
        ]

    # Affichage nettoye (corrige les &#xe9;, &amp;, balises, etc. meme sur d'anciennes donnees).
    @property
    def titre_propre(self):
        return nettoyer_texte(self.titre)

    @property
    def resume_propre(self):
        return nettoyer_texte(self.resume)

    def __str__(self):
        return '{} ({})'.format(self.titre[:60], self.source.nom)


class Brief(models.Model):
    """« Le brief du jour » : synthèse IA quotidienne de la revue de presse."""
    date = models.DateField(unique=True)
    contenu = models.TextField()
    date_generation = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return 'Brief du {}'.format(self.date)
