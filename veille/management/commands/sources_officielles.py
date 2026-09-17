# -*- coding: utf-8 -*-
"""Fixe la liste EXACTE des sources du « mur de la presse » (liste blanche).

Toute source absente de cette liste est supprimee (avec ses items), afin que le
mur n'affiche QUE les sites demandes. Feeds natifs quand ils fonctionnent, sinon
Google Actualités restreint au domaine (`site:domaine`) : jamais de contenu
provenant d'un autre site.

Usage :  python manage.py sources_officielles   (puis  python manage.py ingest)
"""
from urllib.parse import quote

from django.core.management.base import BaseCommand

from veille.models import RevueItem, Source


def gn(domaine):
    """Flux Google Actualités limité à un seul domaine (contenu 100 % de ce site)."""
    return ('https://news.google.com/rss/search?q=' + quote('site:' + domaine)
            + '&hl=fr&gl=SN&ceid=SN:fr')


# (nom affiché, flux RSS, catégorie). Feeds natifs vérifiés le 2026-09-17 ; les
# autres passent par Google Actualités restreint au domaine.
WHITELIST = [
    # --- Presse générale ---
    ('Seneweb', gn('seneweb.com'), 'Presse'),
    ('Leral', 'https://www.leral.net/xml/syndication.rss', 'Presse'),
    ('RTS', gn('rts.sn'), 'Presse'),
    ('Le Soleil', 'https://lesoleil.sn/feed/', 'Presse'),
    ('APS', 'https://aps.sn/feed/', 'Presse'),
    ('Dakaractu', 'https://www.dakaractu.com/xml/syndication.rss', 'Presse'),
    ('Le Quotidien', gn('lequotidien.sn'), 'Presse'),
    ('Libération', gn('liberationonline.sn'), 'Presse'),
    ('IGFM', gn('igfm.sn'), 'Presse'),
    ('Sud Quotidien', gn('sudquotidien.sn'), 'Presse'),
    ("L'Enquête", gn('lenquete.sn'), 'Presse'),
    ('La Maison des Reporters', gn('lamaisondesreporters.com'), 'Presse'),
    ('Africa Check', gn('africacheck.org'), 'Fact-check'),
    # --- Sport ---
    ('Wiwsport', 'https://wiwsport.com/feed/', 'Sport'),
    ('DSports', gn('dsports.sn'), 'Sport'),
    ('FootAfrica', gn('footafrica.com'), 'Sport'),
    ('Foot News Africa', gn('footnewsafrica.com'), 'Sport'),
    ('LSFP', gn('lsfp.sn'), 'Sport'),
    ('Galsenfoot', 'https://www.galsenfoot.com/feed/', 'Sport'),
    ('Fédération Sénégalaise de Football', gn('fsfoot.sn'), 'Sport'),
    # --- Économie ---
    ('Les JECOS', gn('lesjecos.com'), 'Économie'),
    ('Financial Afrik', 'https://www.financialafrik.com/feed/', 'Économie'),
    ('Ola', gn('ola.sn'), 'Économie'),
    # --- Institutions ---
    ('Ministères du Sénégal', gn('gouv.sn'), 'Institution'),
]


class Command(BaseCommand):
    help = "Installe la liste blanche des sources du mur de la presse."

    def handle(self, *args, **options):
        noms = {nom for nom, _, _ in WHITELIST}

        # 1. Supprimer les sources hors liste (et donc leurs items en cascade).
        hors = Source.objects.exclude(nom__in=noms)
        nb_items = RevueItem.objects.filter(source__in=hors).count()
        supprimees = list(hors.values_list('nom', flat=True))
        hors.delete()
        if supprimees:
            self.stdout.write("Sources retirées : {} ({} item(s) supprimé(s))".format(
                ', '.join(supprimees), nb_items))

        # 2. Créer / mettre à jour les sources de la liste blanche.
        for nom, url, cat in WHITELIST:
            obj, cree = Source.objects.get_or_create(nom=nom, defaults={
                'url_rss': url, 'categorie': cat, 'actif': True})
            if not cree:
                obj.url_rss = url
                obj.categorie = cat
                obj.actif = True
                obj.save(update_fields=['url_rss', 'categorie', 'actif'])
            self.stdout.write(('  + ' if cree else '  = ') + nom)

        self.stdout.write(self.style.SUCCESS(
            "Liste blanche installée : {} sources. "
            "Lancez maintenant : python manage.py ingest".format(len(WHITELIST))))
