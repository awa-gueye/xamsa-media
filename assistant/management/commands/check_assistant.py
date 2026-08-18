# -*- coding: utf-8 -*-
"""Diagnostic de l'assistant Looy laaj : cle LLM, recherche web, retrieval.

    python manage.py check_assistant
    python manage.py check_assistant --question "histoire de la presse au Senegal"
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from assistant.engine import est_social
from assistant.llm import LLMIndisponible, generer_reponse
from assistant.retrieval import documents_du_site
from assistant.web_search import documents_du_web


class Command(BaseCommand):
    help = "Verifie la configuration de l'assistant (LLM, recherche web, contenu)."

    def add_arguments(self, parser):
        parser.add_argument('--question', default='presse senegalaise')

    def handle(self, *args, **options):
        q = options['question']
        ok = self.style.SUCCESS
        ko = self.style.ERROR
        warn = self.style.WARNING

        provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
        if provider == 'groq':
            cle = getattr(settings, 'GROQ_API_KEY', '')
            modele = getattr(settings, 'GROQ_MODEL', '?')
            nom_cle, lien_cle = 'GROQ_API_KEY', 'https://console.groq.com/keys'
        else:
            cle = getattr(settings, 'GEMINI_API_KEY', '')
            modele = getattr(settings, 'GEMINI_MODEL', '?')
            nom_cle, lien_cle = 'GEMINI_API_KEY', 'https://aistudio.google.com/apikey'

        self.stdout.write("== Configuration ==")
        self.stdout.write("LLM_PROVIDER        : {}".format(provider))
        self.stdout.write("Modele              : {}".format(modele))
        self.stdout.write("{:<19} : {}".format(nom_cle,
            ok("definie ({} car.)".format(len(cle))) if cle else ko("ABSENTE")))
        self.stdout.write("WEB_SEARCH_ENABLED  : {}".format(
            getattr(settings, 'WEB_SEARCH_ENABLED', True)))

        self.stdout.write("\n== Contenu du site ==")
        docs_site = documents_du_site(q)
        self.stdout.write("Documents trouves   : {}".format(len(docs_site)))

        self.stdout.write("\n== Recherche web (DuckDuckGo) ==")
        docs_web = documents_du_web(q)
        if docs_web:
            self.stdout.write(ok("OK, {} resultat(s).".format(len(docs_web))))
        else:
            self.stdout.write(warn("Aucun resultat (desactivee, hors ligne, ou ddgs absent)."))

        self.stdout.write("\n== Appel LLM ==")
        if not cle:
            self.stdout.write(ko(
                "Pas de cle : l'assistant fonctionnera en mode repli (liste de liens)."))
            self.stdout.write(
                "-> Cle gratuite sur {}, puis {}=... dans le fichier .env "
                "a la racine.".format(lien_cle, nom_cle))
            return
        try:
            texte, indices = generer_reponse(q, docs_site + docs_web)
            self.stdout.write(ok("LLM operationnel."))
            self.stdout.write("Message social ?    : {}".format(est_social(q)))
            self.stdout.write("Sources citees      : {}".format(len(indices)))
            self.stdout.write("\nReponse :\n{}".format(texte))
        except LLMIndisponible as exc:
            self.stdout.write(ko("Echec de l'appel LLM : {}".format(exc)))
            self.stdout.write(warn(
                "Verifiez la cle, le nom du modele, ou votre acces reseau/quota."))
