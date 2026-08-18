# -*- coding: utf-8 -*-
"""Génère « Le brief du jour » à partir de la revue de presse.

    python manage.py generer_brief            (une fois par jour)
    python manage.py generer_brief --force    (régénère même si déjà présent)
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Génère le brief du jour (synthèse IA de la revue de presse)."

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true')

    def handle(self, *args, **options):
        from assistant.brief import generer_brief_du_jour
        brief = generer_brief_du_jour(force=options['force'])
        if brief:
            self.stdout.write(self.style.SUCCESS('Brief du {} genere.'.format(brief.date)))
            self.stdout.write(brief.contenu)
        else:
            self.stdout.write(self.style.WARNING(
                "Aucun brief genere (pas assez d'actualite ou LLM indisponible)."))
