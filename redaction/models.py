"""Contenu editorial produit par Xamsa Media : rubriques, enquetes, dossiers."""
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Categorie(models.Model):
    nom = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'
        ordering = ['nom']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Article(models.Model):
    TYPE_ENQUETE = 'enquete'
    TYPE_REPORTAGE = 'reportage'
    TYPE_DOSSIER = 'dossier'
    TYPE_ANALYSE = 'analyse'
    TYPES = [
        (TYPE_ENQUETE, 'Enquete'),
        (TYPE_REPORTAGE, 'Reportage'),
        (TYPE_DOSSIER, 'Dossier'),
        (TYPE_ANALYSE, 'Analyse'),
    ]

    titre = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPES, default=TYPE_ENQUETE)
    categorie = models.ForeignKey(
        Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles'
    )
    chapo = models.TextField('Chapo (accroche)', blank=True)
    corps = models.TextField('Corps de l\'article', blank=True)
    image = models.ImageField('Image (fichier)', upload_to='articles/', blank=True, null=True)
    image_url = models.URLField('Image (URL externe)', max_length=600, blank=True)
    temps_lecture = models.PositiveIntegerField('Temps de lecture (min)', default=6)
    a_la_une = models.BooleanField('A la une', default=False)
    publie = models.BooleanField('Publie', default=True)
    date_publication = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date_publication']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre)[:240]
        super().save(*args, **kwargs)

    @property
    def visuel(self):
        """URL de l'image a afficher : fichier envoye, sinon URL externe."""
        if self.image:
            return self.image.url
        return self.image_url

    def get_absolute_url(self):
        return reverse('article_detail', args=[self.slug])

    def __str__(self):
        return self.titre
