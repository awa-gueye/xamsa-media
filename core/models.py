# -*- coding: utf-8 -*-
"""Modeles transverses du site (lettre d'information)."""
from django.db import models


class AbonneNewsletter(models.Model):
    """Adresse inscrite à la lettre d'information depuis le pied de page."""
    email = models.EmailField('Adresse email', unique=True)
    actif = models.BooleanField('Actif', default=True)
    date = models.DateTimeField('Inscrit le', auto_now_add=True)

    class Meta:
        verbose_name = "Abonné à la newsletter"
        verbose_name_plural = "Abonnés à la newsletter"
        ordering = ['-date']

    def __str__(self):
        return self.email
