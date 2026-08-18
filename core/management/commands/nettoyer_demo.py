# -*- coding: utf-8 -*-
"""Retire les anciennes donnees de demonstration (illustratives).

Supprime uniquement les contenus fictifs connus (par leur titre ou URL exacte).
PRESERVE : les categories, les sources RSS, la revue de presse reelle issue de
l'ingestion RSS, les contributions des utilisateurs et les comptes.

Usage : python manage.py nettoyer_demo
"""
from django.core.management.base import BaseCommand

from espaces.models import ItemCommunaute, MediaSenegal, Ressource
from multimedia.models import Media
from redaction.models import Article
from veille.models import RevueItem

# Titres exacts des anciens contenus de demonstration.
ARTICLES_DEMO = [
    'Le pétrole sénégalais entre dans une nouvelle phase : ce que les chiffres racontent',
    "Économie des médias : radiographie d'un secteur sous tension",
    "Sur le littoral, la lente disparition d'un village de pêcheurs",
    "Marchés publics : sur la piste des contrats attribués sans appel d'offres",
    'Déserts médicaux : la carte que personne ne montre',
    "Fonds politiques : à quoi sert vraiment l'argent public ?",
    "Numérique : ces créateurs qui réinventent l'information",
    "Dakar, capitale culturelle : la scène qui s'impose en Afrique",
]
MEDIAS_DEMO = [
    'Les gardiens du fleuve : une saison sur le Sénégal',
    "Dakar au travail : portraits de l'économie informelle",
    'Terres du Sine : la mémoire des villages',
    "Looy laaj ? L'entretien de la semaine",
    'Titraille : la revue de presse en audio',
    "Data Sénégal : les chiffres derrière l'info",
]
RESSOURCES_DEMO = [
    "Initiation au journalisme d'investigation",
    'Fact-checking et lutte contre la désinformation',
    'Couvrir une élection en toute sécurité',
    'Guide de la déontologie de la presse',
    'Certificat de reporter numérique',
]
COMMU_DEMO = [
    'Proposez votre sujet à la rédaction',
    'Prix du jeune reporter 2026',
    'Synpics : le syndicat des professionnels',
    'Bourse de formation au reportage',
    'Offre : journaliste multimédia',
]
MEDIASN_DEMO = [
    'Une histoire de la presse sénégalaise',
    'Portrait : une grande signature de la presse',
    'Panorama des chaînes de télévision',
    'Le paysage radiophonique sénégalais',
    'La presse écrite au Sénégal',
    'Les médias numériques qui montent',
    "La vague des podcasts d'info",
]
# URLs exactes des items de revue fictifs (les vrais ont des URL d'articles completes).
REVUE_DEMO_URLS = [
    'https://www.senenews.com', 'https://senegal7.com', 'http://www.adakar.com',
    'https://fr.allafrica.com', 'https://www.rfi.fr', 'https://www.france24.com',
]


class Command(BaseCommand):
    help = 'Supprime les anciennes donnees de demonstration (preserve le contenu reel).'

    def handle(self, *args, **options):
        total = 0
        for modele, champ, valeurs in [
            (Article, 'titre__in', ARTICLES_DEMO),
            (Media, 'titre__in', MEDIAS_DEMO),
            (Ressource, 'titre__in', RESSOURCES_DEMO),
            (ItemCommunaute, 'titre__in', COMMU_DEMO),
            (MediaSenegal, 'titre__in', MEDIASN_DEMO),
            (RevueItem, 'url__in', REVUE_DEMO_URLS),
        ]:
            n, _ = modele.objects.filter(**{champ: valeurs}).delete()
            total += n
            self.stdout.write('  {} : {} objet(s) supprime(s)'.format(modele.__name__, n))
        self.stdout.write(self.style.SUCCESS(
            '{} objet(s) de demonstration supprime(s). Contenu reel preserve.'.format(total)))
