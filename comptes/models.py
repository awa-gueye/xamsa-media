# -*- coding: utf-8 -*-
"""Profils utilisateurs adaptes a un media (pas de RH)."""
from django.contrib.auth.models import User
from django.db import models


class Profil(models.Model):
    LECTEUR = 'lecteur'
    JOURNALISTE = 'journaliste'
    ETUDIANT = 'etudiant'
    ORGANE = 'organe'
    TYPES = [
        (LECTEUR, 'Lecteur / Citoyen'),
        (JOURNALISTE, 'Journaliste / Contributeur'),
        (ETUDIANT, "Étudiant de l'Académie"),
        (ORGANE, 'Organe de presse / Association'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    type_profil = models.CharField(max_length=20, choices=TYPES, default=LECTEUR)
    de_confiance = models.BooleanField(
        'Contributeur de confiance',
        help_text="Ses contributions jugées bonnes sont publiées automatiquement.",
        default=False)
    telephone = models.CharField(max_length=30, blank=True)
    localisation = models.CharField(max_length=120, blank=True)
    organisation = models.CharField(max_length=160, blank=True)
    photo = models.ImageField('Photo de profil', upload_to='profils/', blank=True, null=True)
    bio = models.TextField(blank=True)
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} ({})'.format(self.user.get_full_name() or self.user.username, self.get_type_profil_display())


class Contribution(models.Model):
    """Contenu proposé par un utilisateur (selon son profil), soumis à validation."""
    TYPES = [
        ('sujet', 'Proposition de sujet'),
        ('article', 'Article'),
        ('rapport', 'Rapport / dossier'),
        ('tribune', 'Tribune / analyse'),
        ('audio', 'Audio'),
        ('video', 'Vidéo'),
    ]
    STATUTS = [('attente', 'En attente de validation'), ('publie', 'Publié'), ('refuse', 'Refusé')]

    # Ce que chaque profil a le droit de publier.
    TYPES_PAR_PROFIL = {
        'lecteur': ['sujet'],
        'etudiant': ['sujet', 'tribune'],
        'journaliste': ['article', 'rapport', 'tribune', 'audio', 'video', 'sujet'],
        'organe': ['article', 'rapport', 'tribune', 'audio', 'video', 'sujet'],
    }

    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    type = models.CharField(max_length=20, choices=TYPES, default='sujet')
    titre = models.CharField(max_length=240)
    categorie = models.CharField(max_length=60, blank=True)
    resume = models.TextField('Résumé', blank=True)
    corps = models.TextField('Contenu', blank=True)
    image = models.ImageField('Image de la publication', upload_to='contributions/images/', blank=True, null=True)
    fichier = models.FileField('Fichier (audio, vidéo, document)', upload_to='contributions/fichiers/', blank=True, null=True)
    statut = models.CharField(max_length=12, choices=STATUTS, default='attente')
    vues = models.PositiveIntegerField('Nombre de vues', default=0)
    # Pré-modération IA : verdict, score de confiance (0-100) et justification courte.
    VERDICTS = [('', 'Non évalué'), ('publier', 'Recommandé'),
                ('reviser', 'À vérifier'), ('rejeter', 'À rejeter')]
    moderation_verdict = models.CharField(max_length=10, choices=VERDICTS, blank=True, default='')
    moderation_score = models.PositiveIntegerField(default=0)
    moderation_note = models.CharField(max_length=300, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return '{} — {}'.format(self.get_type_display(), self.titre)

    @property
    def corps_html(self):
        """Corps rendu en HTML sur pour l'affichage (assaini a chaque rendu).

        Le contenu de l'editeur enrichi est deja du HTML ; les anciennes
        contributions en texte simple sont converties en paragraphes.
        """
        from django.utils.html import escape, linebreaks
        from django.utils.safestring import mark_safe

        from .sanitize import nettoyer_html
        corps = (self.corps or '').strip()
        if '<' in corps and '>' in corps:
            return mark_safe(nettoyer_html(corps))
        return mark_safe(linebreaks(escape(corps)))

    @property
    def temps_lecture(self):
        """Estimation du temps de lecture en minutes (~200 mots/min)."""
        import re
        texte = re.sub(r'<[^>]+>', ' ', self.corps or '')
        mots = len(texte.split())
        return max(1, round(mots / 200))

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('publication_detail', args=[self.pk])


class Commentaire(models.Model):
    """Commentaire d'un utilisateur sur une publication (fil : 1 niveau de réponse)."""
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commentaires')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='reponses')
    texte = models.TextField('Commentaire')
    masque = models.BooleanField('Masqué (modération)', default=False)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return 'Commentaire de {} sur {}'.format(self.auteur, self.contribution_id)

    @property
    def reponses_visibles(self):
        return self.reponses.filter(masque=False).select_related('auteur', 'auteur__profil')


class Reaction(models.Model):
    """« J'aime » d'un utilisateur sur une publication (une seule par personne)."""
    JAIME = 'jaime'
    TYPES = [(JAIME, "J'aime")]

    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE, related_name='reactions')
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    type = models.CharField(max_length=12, choices=TYPES, default=JAIME)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['contribution', 'auteur'], name='reaction_unique_par_personne'),
        ]

    def __str__(self):
        return '{} aime {}'.format(self.auteur, self.contribution_id)


class Notification(models.Model):
    """Notification à l'auteur : commentaire, réponse ou J'aime sur sa publication."""
    COMMENTAIRE = 'commentaire'
    REPONSE = 'reponse'
    JAIME = 'jaime'
    TYPES = [(COMMENTAIRE, 'Commentaire'), (REPONSE, 'Réponse'), (JAIME, "J'aime")]

    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    acteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_emises')
    type = models.CharField(max_length=12, choices=TYPES)
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE, related_name='notifications')
    commentaire = models.ForeignKey(Commentaire, on_delete=models.SET_NULL, null=True, blank=True)
    lu = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return 'Notif {} pour {}'.format(self.type, self.destinataire)

    @staticmethod
    def creer(destinataire, acteur, type, contribution, commentaire=None):
        """Cree une notification, sauf si on se notifie soi-meme."""
        if destinataire and acteur and destinataire != acteur:
            Notification.objects.create(destinataire=destinataire, acteur=acteur, type=type,
                                        contribution=contribution, commentaire=commentaire)


class Favori(models.Model):
    """Publication mise de côté par un utilisateur (« lire plus tard »)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris')
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE, related_name='favoris')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(fields=['user', 'contribution'], name='favori_unique_par_personne'),
        ]

    def __str__(self):
        return '{} -> {}'.format(self.user, self.contribution_id)
