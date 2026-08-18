# -*- coding: utf-8 -*-
"""Donnees structurelles reelles de Xamsa Media.

Insere uniquement du contenu reel et verifiable :
- les categories editoriales ;
- les sources RSS (qui alimentent la vraie revue de presse via `ingest`) ;
- un annuaire des medias senegalais (chaines TV, radios, presse, numerique) ;
- les principales associations et instances de la presse senegalaise.

Il n'insere AUCUN faux article, faux dossier ni faux contenu de demonstration :
ces contenus sont crees par la redaction depuis l'administration.

Usage : python manage.py seed   (idempotent : get_or_create)
Pour retirer d'anciennes donnees de demonstration : python manage.py nettoyer_demo
"""
from django.core.management.base import BaseCommand
from django.templatetags.static import static

from espaces.models import ItemCommunaute, MediaSenegal
from redaction.models import Categorie
from veille.models import Source

CATEGORIES = ['Investigation', 'Économie', 'Politique', 'Environnement',
              'Science & Tech', 'Santé', 'Culture & Religion', 'Sport']

SOURCES = [
    ('SeneNews', 'https://www.senenews.com/feed', 'Web', 'https://www.senenews.com'),
    ('Sénégal7', 'https://senegal7.com/feed/', 'Web', 'https://senegal7.com'),
    ('aDakar', 'http://news.adakar.com/xml/all.xml', 'Agrégateur', 'http://www.adakar.com'),
    ('Google Actu Sénégal',
     'https://news.google.com/rss/search?q=S%C3%A9n%C3%A9gal&hl=fr&gl=SN&ceid=SN:fr',
     'Agrégateur', 'https://news.google.com'),
    ('AllAfrica Sénégal',
     'https://fr.allafrica.com/tools/headlines/rdf/senegal/headlines.rdf',
     'Panafricain', 'https://fr.allafrica.com'),
    ('RFI Sénégal', 'https://www.rfi.fr/fr/tag/s%C3%A9n%C3%A9gal/rss', 'International', 'https://www.rfi.fr'),
    ('France24 Sénégal', 'https://www.france24.com/fr/tag/s%C3%A9n%C3%A9gal/rss', 'International', 'https://www.france24.com'),
]

# Annuaire des medias senegalais reels. (titre, type, description, meta, lien, illustration)
MEDIAS_SENEGAL = [
    # Chaines de television
    ('RTS1', 'tv', "Chaîne de télévision publique nationale, opérée par la Radiodiffusion "
     "Télévision Sénégalaise.", 'Télévision publique', 'https://www.rts.sn', 'media'),
    ('TFM', 'tv', "Chaîne de télévision privée généraliste du Groupe Futurs Médias.",
     'Télévision privée', 'https://www.tfm.sn', 'media'),
    ('2STV', 'tv', "Chaîne de télévision privée généraliste, l'une des premières télévisions "
     "privées du pays.", 'Télévision privée', 'https://www.2stv.tv', 'media'),
    ('Walf TV', 'tv', "Chaîne de télévision du Groupe Walfadjri, l'un des plus anciens groupes "
     "de presse privés du Sénégal.", 'Télévision privée', 'https://www.walf-groupe.com', 'media'),
    ('SEN TV', 'tv', "Chaîne de télévision privée du groupe D-Media.",
     'Télévision privée', '', 'media'),
    ('7TV', 'tv', "Chaîne de télévision privée à dominante information et magazines.",
     'Télévision privée', '', 'media'),
    # Radios
    ('RFM (Radio Futurs Médias)', 'radio', "Radio généraliste privée du Groupe Futurs Médias, "
     "l'une des plus écoutées du pays.", 'Radio privée', 'https://www.rfm.sn', 'radio'),
    ('Sud FM', 'radio', "Radio d'information du Groupe Sud Communication, pionnière des radios "
     "privées au Sénégal.", 'Radio privée', 'https://www.sudfm.sn', 'radio'),
    ('Walf FM', 'radio', "Radio d'information du Groupe Walfadjri.",
     'Radio privée', 'https://www.walf-groupe.com', 'radio'),
    ('Zik FM', 'radio', "Radio généraliste et musicale du Groupe Futurs Médias.",
     'Radio privée', '', 'radio'),
    ('iRadio', 'radio', "Radio d'information privée du groupe D-Media.",
     'Radio privée', '', 'radio'),
    ('Radio Sénégal (RTS)', 'radio', "Radio publique nationale de la Radiodiffusion Télévision "
     "Sénégalaise.", 'Radio publique', 'https://www.rts.sn', 'radio'),
    # Presse ecrite
    ('Le Soleil', 'presse', "Quotidien national à capitaux publics, fondé en 1970.",
     'Quotidien', 'https://lesoleil.sn', 'media'),
    ('Walf Quotidien', 'presse', "Quotidien d'information du Groupe Walfadjri.",
     'Quotidien', 'https://www.walf-groupe.com', 'media'),
    ('Sud Quotidien', 'presse', "Quotidien d'information du Groupe Sud Communication.",
     'Quotidien', 'https://www.sudquotidien.sn', 'media'),
    ("L'Observateur", 'presse', "Quotidien d'information du Groupe Futurs Médias.",
     'Quotidien', '', 'media'),
    ('Le Quotidien', 'presse', "Quotidien d'information généraliste.",
     'Quotidien', 'https://www.lequotidien.sn', 'media'),
    ('EnQuête', 'presse', "Quotidien d'information et d'analyse.",
     'Quotidien', 'https://www.enqueteplus.com', 'media'),
    # Medias numeriques
    ('Seneweb', 'numerique', "Portail d'information généraliste, l'un des sites les plus "
     "consultés du Sénégal.", 'Pure player', 'https://www.seneweb.com', 'tech'),
    ('SeneNews', 'numerique', "Site d'actualité généraliste.",
     'Pure player', 'https://www.senenews.com', 'tech'),
    ('Dakaractu', 'numerique', "Site d'information en continu.",
     'Pure player', 'https://www.dakaractu.com', 'tech'),
    ('PressAfrik', 'numerique', "Site d'information indépendant.",
     'Pure player', 'https://www.pressafrik.com', 'tech'),
    ('Senego', 'numerique', "Site d'actualité généraliste.",
     'Pure player', 'https://senego.com', 'tech'),
]

# Instances et associations de la presse senegalaise. (titre, description, meta, lien)
ASSOCIATIONS = [
    ('SYNPICS', "Syndicat des professionnels de l'information et de la communication du "
     "Sénégal, principale organisation syndicale des journalistes.", 'Syndicat', ''),
    ('CORED', "Conseil pour l'observation des règles d'éthique et de déontologie dans les "
     "médias, instance d'autorégulation de la presse sénégalaise.", 'Autorégulation', ''),
    ('CJRS', "Convention des jeunes reporters du Sénégal, association des jeunes "
     "professionnels des médias.", 'Association', ''),
    ('CDEPS', "Conseil des diffuseurs et éditeurs de presse du Sénégal, organisation "
     "patronale des entreprises de presse.", 'Patronat de presse', ''),
    ('APPEL', "Association des professionnels de la presse en ligne, qui fédère les "
     "acteurs des médias numériques.", 'Association', ''),
]


def img(nom):
    return static('img/cat/{}.svg'.format(nom))


class Command(BaseCommand):
    help = 'Insere les donnees structurelles reelles (categories, sources, annuaire medias).'

    def handle(self, *args, **options):
        for nom in CATEGORIES:
            Categorie.objects.get_or_create(nom=nom)

        for nom, rss, cat, site in SOURCES:
            Source.objects.get_or_create(
                nom=nom, defaults={'url_rss': rss, 'categorie': cat, 'site': site})

        for titre, typ, desc, meta, lien, illus in MEDIAS_SENEGAL:
            MediaSenegal.objects.get_or_create(
                titre=titre, defaults={'type': typ, 'description': desc, 'meta': meta,
                                       'lien': lien, 'image_url': img(illus)})

        for titre, desc, meta, lien in ASSOCIATIONS:
            ItemCommunaute.objects.get_or_create(
                titre=titre, defaults={'type': 'association', 'description': desc,
                                       'meta': meta, 'lien': lien, 'image_url': img('societe')})

        # Import automatique des logos des medias (depuis static/img/medias-src).
        try:
            from django.core.management import call_command
            call_command('importer_logos', verbosity=0)
        except Exception as exc:
            self.stdout.write(self.style.WARNING('Logos non importes : {}'.format(exc)))

        self.stdout.write(self.style.SUCCESS(
            'Donnees structurelles reelles inserees (categories, sources, medias, associations).'))
