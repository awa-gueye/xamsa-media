# -*- coding: utf-8 -*-
"""Diagnostic email : montre la configuration active et tente un envoi reel.

Usage :  python manage.py test_email destinataire@exemple.com
Sans argument, envoie a DEFAULT_FROM_EMAIL / ADMIN_EMAIL.
A lancer en local ou dans le shell Render pour savoir, sans ambiguite, si
l'envoi fonctionne et, sinon, quelle est l'erreur exacte.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Affiche la config email et envoie un email de test."

    def add_arguments(self, parser):
        parser.add_argument('destinataire', nargs='?', default='')

    def handle(self, *args, **options):
        dest = (options.get('destinataire') or '').strip()
        if not dest:
            dest = getattr(settings, 'ADMIN_EMAIL', '') or settings.DEFAULT_FROM_EMAIL

        self.stdout.write("=== Configuration email active ===")
        self.stdout.write("EMAIL_BACKEND      : {}".format(settings.EMAIL_BACKEND))
        self.stdout.write("EMAIL_ACTIF        : {}".format(getattr(settings, 'EMAIL_ACTIF', None)))
        self.stdout.write("BREVO_API_KEY      : {}".format(
            'defini ({} caracteres)'.format(len(settings.BREVO_API_KEY))
            if getattr(settings, 'BREVO_API_KEY', '') else 'absent'))
        self.stdout.write("EMAIL_HOST         : {}".format(getattr(settings, 'EMAIL_HOST', '') or 'absent'))
        self.stdout.write("EMAIL_HOST_USER    : {}".format(getattr(settings, 'EMAIL_HOST_USER', '') or 'absent'))
        pw = getattr(settings, 'EMAIL_HOST_PASSWORD', '') or ''
        self.stdout.write("EMAIL_HOST_PASSWORD: {}".format(
            '{} caracteres'.format(len(pw)) if pw else 'absent'))
        self.stdout.write("DEFAULT_FROM_EMAIL : {}".format(settings.DEFAULT_FROM_EMAIL))

        if 'console' in settings.EMAIL_BACKEND:
            self.stdout.write(self.style.WARNING(
                "\nATTENTION : backend CONSOLE actif -> aucun email reel n'est envoye. "
                "Definissez BREVO_API_KEY (recommande) ou EMAIL_HOST_PASSWORD."))

        self.stdout.write("\nEnvoi d'un test a : {} ...".format(dest))
        try:
            n = send_mail(
                "Xamsa Média — test de configuration email",
                "Cet email confirme que l'envoi fonctionne. "
                "Si vous le recevez, la reinitialisation de mot de passe fonctionnera aussi.",
                settings.DEFAULT_FROM_EMAIL, [dest], fail_silently=False)
            self.stdout.write(self.style.SUCCESS(
                "OK : {} email(s) accepte(s) par le serveur. "
                "Verifiez la boite de reception ET le dossier spam.".format(n)))
        except Exception as exc:  # noqa: BLE001 — on veut afficher toute erreur
            self.stdout.write(self.style.ERROR(
                "ECHEC : {} : {}".format(type(exc).__name__, exc)))
