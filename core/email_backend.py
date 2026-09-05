# -*- coding: utf-8 -*-
"""Backend d'envoi d'email via l'API HTTP de Brevo (ex-Sendinblue).

Pourquoi : l'envoi SMTP (Gmail) depuis un hebergeur est fragile (port parfois
bloque, mot de passe d'application a maintenir, mises en spam). L'API HTTP de
Brevo passe par HTTPS (port 443, jamais bloque) et est fiable depuis un serveur.

Activation : definir `BREVO_API_KEY`. L'expediteur est `DEFAULT_FROM_EMAIL`
(l'adresse doit etre validee comme expediteur dans le compte Brevo).

Ce backend implemente l'interface standard Django : il fonctionne donc tel quel
avec la reinitialisation de mot de passe et tout `send_mail`.
"""
import logging

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address

logger = logging.getLogger(__name__)

_API_URL = 'https://api.brevo.com/v3/smtp/email'
_TIMEOUT = 20


def _parse_expediteur(from_email):
    """('Xamsa Média <x@y.com>') -> {'name': 'Xamsa Média', 'email': 'x@y.com'}."""
    from email.utils import parseaddr
    nom, adresse = parseaddr(from_email or '')
    exp = {'email': adresse or from_email}
    if nom:
        exp['name'] = nom
    return exp


class BrevoAPIBackend(BaseEmailBackend):
    """Envoie les EmailMessage Django via l'API transactionnelle de Brevo."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError("BREVO_API_KEY absente : impossible d'envoyer l'email.")
            return 0
        envoyes = 0
        for message in email_messages:
            if self._envoyer_un(message):
                envoyes += 1
        return envoyes

    def _envoyer_un(self, message):
        expediteur = _parse_expediteur(message.from_email)
        destinataires = [{'email': sanitize_address(a, message.encoding)}
                         for a in message.recipients()]
        if not destinataires:
            return False

        # Corps texte + eventuelle alternative HTML.
        texte = message.body or ''
        html = ''
        for contenu, mimetype in getattr(message, 'alternatives', []) or []:
            if mimetype == 'text/html':
                html = contenu
                break
        if getattr(message, 'content_subtype', 'plain') == 'html':
            html = html or texte

        charge = {
            'sender': expediteur,
            'to': destinataires,
            'subject': message.subject,
            'textContent': texte or ' ',
        }
        if html:
            charge['htmlContent'] = html
        if message.reply_to:
            charge['replyTo'] = _parse_expediteur(message.reply_to[0])

        try:
            rep = requests.post(_API_URL, json=charge, timeout=_TIMEOUT, headers={
                'api-key': self.api_key, 'accept': 'application/json',
                'content-type': 'application/json'})
        except requests.RequestException as exc:
            logger.error("Brevo : erreur reseau : %s", exc)
            if not self.fail_silently:
                raise
            return False

        if rep.status_code not in (200, 201, 202):
            logger.error("Brevo a repondu %s : %s", rep.status_code, rep.text[:300])
            if not self.fail_silently:
                raise RuntimeError("Brevo a repondu {} : {}".format(
                    rep.status_code, rep.text[:200]))
            return False
        return True
