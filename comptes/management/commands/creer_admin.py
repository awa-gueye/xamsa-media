# -*- coding: utf-8 -*-
"""Cree le compte administrateur depuis les variables d'environnement.

Utile sur les hebergeurs sans shell (Render gratuit) : `createsuperuser` est
interactif et donc inutilisable. On lit ADMIN_EMAIL et ADMIN_PASSWORD.

    python manage.py creer_admin

Idempotent : si l'administrateur existe deja, on ne touche pas a son mot de passe
(pour ne pas l'ecraser a chaque redeploiement). Passez --reset-password pour le
forcer a la valeur de ADMIN_PASSWORD.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cree l'administrateur depuis ADMIN_EMAIL / ADMIN_PASSWORD."

    def add_arguments(self, parser):
        parser.add_argument('--reset-password', action='store_true',
                            help="Reinitialise le mot de passe de l'admin existant.")

    def handle(self, *args, **options):
        email = os.environ.get('ADMIN_EMAIL', '').strip()
        password = os.environ.get('ADMIN_PASSWORD', '')
        if not email or not password:
            self.stdout.write(self.style.WARNING(
                "ADMIN_EMAIL / ADMIN_PASSWORD non definis : administrateur non cree."))
            return

        User = get_user_model()
        user = (User.objects.filter(username__iexact=email).first()
                or User.objects.filter(email__iexact=email).first())
        if user:
            change = False
            if not (user.is_staff and user.is_superuser):
                user.is_staff = user.is_superuser = True
                change = True
            if options['reset_password']:
                user.set_password(password)
                change = True
            if change:
                user.save()
            self.stdout.write(self.style.SUCCESS(
                "Administrateur deja present : {} (inchange).".format(email)))
        else:
            User.objects.create_superuser(username=email, email=email, password=password)
            self.stdout.write(self.style.SUCCESS("Administrateur cree : {}".format(email)))
