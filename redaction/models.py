"""Contenu editorial produit par Xamsa Media : rubriques, enquetes, dossiers."""
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Categorie(models.Model):
    nom = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    image = models.ImageField('Image (fichier)', upload_to='rubriques/', blank=True, null=True)
    image_url = models.URLField('Image (URL externe)', max_length=600, blank=True,
                                help_text="Image illustrant la rubrique (remplace l'icône).")

    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'
        ordering = ['nom']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    @property
    def visuel(self):
        if self.image:
            return self.image.url
        return self.image_url

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
    video_url = models.URLField('Vidéo YouTube (URL)', max_length=600, blank=True,
                                help_text="Lien YouTube : la vidéo sera affichée dans l'article.")
    temps_lecture = models.PositiveIntegerField('Temps de lecture (min)', default=6)
    a_la_une = models.BooleanField('A la une', default=False)
    derniere_minute = models.BooleanField(
        'Dernière minute (carrousel accueil)', default=False,
        help_text="Affiche cette publication dans le carrousel « Dernière minute » de l'accueil.")
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

    @property
    def video_embed(self):
        """URL d'integration YouTube (iframe) si une video est renseignee."""
        from core.media_embed import youtube_embed
        return youtube_embed(self.video_url)

    def get_absolute_url(self):
        return reverse('article_detail', args=[self.slug])

    def __str__(self):
        return self.titre


class ArticleCommentaire(models.Model):
    """Commentaire d'un lecteur sur un article (fil à 1 niveau de réponses)."""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commentaires_articles')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='reponses')
    texte = models.TextField('Commentaire')
    masque = models.BooleanField('Masqué (modération)', default=False)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    @property
    def reponses_visibles(self):
        return self.reponses.filter(masque=False).select_related('auteur', 'auteur__profil')

    def __str__(self):
        return '{} — {}'.format(self.auteur, self.texte[:40])


class ArticleJaime(models.Model):
    """« J'aime » d'un utilisateur sur un article (un seul par personne)."""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='jaimes')
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jaimes_articles')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['article', 'auteur'], name='articlejaime_unique'),
        ]

    def __str__(self):
        return '{} ♥ {}'.format(self.auteur, self.article)
