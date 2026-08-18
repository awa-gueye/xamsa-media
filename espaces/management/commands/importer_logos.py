# -*- coding: utf-8 -*-
"""Importe les logos des medias dans le champ `logo` de MediaSenegal.

    python manage.py importer_logos                       (dossier par defaut)
    python manage.py importer_logos --source "C:\\chemin\\vers\\logos"

Associe chaque fichier au bon media par un nom normalise (sans accents, espaces
ni ponctuation). Les images sont converties en PNG dans MEDIA_ROOT/logos/.
"""
import io
import os
import unicodedata

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from django.conf import settings

from espaces.models import MediaSenegal

# Logos versionnes avec le projet (self-contained, re-importables apres reset).
DOSSIER_DEFAUT = os.path.join(settings.BASE_DIR, 'static', 'img', 'medias-src')

# Titre exact du media (en base) -> cle normalisee du fichier logo.
MAPPING = {
    'RTS1': 'rts1',
    'TFM': 'tfm',
    '2STV': '2stv',
    'Walf TV': 'walftv',
    'SEN TV': 'sentv',
    '7TV': '7tv',
    'RFM (Radio Futurs Médias)': 'rfm',
    'Sud FM': 'sudfm',
    'Walf FM': 'walffm',
    'Zik FM': 'zikfm',
    'iRadio': 'iradio',
    'Radio Sénégal (RTS)': 'radiosenegal',
    'Le Soleil': 'lesoleil',
    'Walf Quotidien': 'walf',
    'Sud Quotidien': 'sudquotidien',
    "L'Observateur": 'lobservateur',
    'Le Quotidien': 'lequotidien',
    'EnQuête': 'enquete',
    'Seneweb': 'seneweb',
    'SeneNews': 'senenews',
    'Dakaractu': 'dakaractu',
    'PressAfrik': 'pressafrik',
    'Senego': 'senego',
}


def _cle(nom):
    """Normalise : minuscules, sans accents, sans espaces ni ponctuation."""
    nom = unicodedata.normalize('NFD', nom.lower())
    nom = ''.join(c for c in nom if unicodedata.category(c) != 'Mn')
    return ''.join(c for c in nom if c.isalnum())


class Command(BaseCommand):
    help = "Importe les logos des medias senegalais dans le champ logo."

    def add_arguments(self, parser):
        parser.add_argument('--source', default=DOSSIER_DEFAUT)

    def handle(self, *args, **options):
        from PIL import Image
        source = options['source']
        if not os.path.isdir(source):
            self.stderr.write(self.style.ERROR("Dossier introuvable : {}".format(source)))
            return

        # Index des fichiers du dossier source par cle normalisee (sans extension).
        fichiers = {}
        for f in os.listdir(source):
            chemin = os.path.join(source, f)
            if os.path.isfile(chemin):
                fichiers[_cle(os.path.splitext(f)[0])] = chemin

        # Stockage permanent (Cloudinary) : inutile de re-uploader a chaque build.
        from django.core.files.storage import default_storage
        persistant = 'cloudinary' in type(default_storage).__module__.lower()

        ok, ignores, absents_media, absents_fichier = 0, 0, [], []
        for titre, cle in MAPPING.items():
            media = MediaSenegal.objects.filter(titre=titre).first()
            if not media:
                absents_media.append(titre)
                continue
            # Sur stockage permanent, si le logo est deja la, on ne le renvoie pas.
            if persistant and media.logo:
                ignores += 1
                continue
            chemin = fichiers.get(cle)
            if not chemin:
                absents_fichier.append('{} ({})'.format(titre, cle))
                continue
            # Conversion en PNG (preserve la transparence eventuelle).
            image = Image.open(chemin)
            image = image.convert('RGBA') if image.mode in ('P', 'RGBA', 'LA') else image.convert('RGB')
            tampon = io.BytesIO()
            image.save(tampon, format='PNG')
            media.logo.save('{}.png'.format(cle), ContentFile(tampon.getvalue()), save=True)
            ok += 1
            self.stdout.write('  logo -> {}'.format(titre))

        self.stdout.write(self.style.SUCCESS(
            '\n{} logo(s) importe(s){}.'.format(
                ok, ' ; {} deja presents (cloud)'.format(ignores) if ignores else '')))
        if absents_media:
            self.stdout.write(self.style.WARNING('Medias absents en base : ' + ', '.join(absents_media)))
        if absents_fichier:
            self.stdout.write(self.style.WARNING('Fichiers logo introuvables : ' + ', '.join(absents_fichier)))
