# -*- coding: utf-8 -*-
"""Validation des fichiers envoyés (anti-abus) : taille et extensions autorisées."""
import os

from django.core.exceptions import ValidationError

MAX_IMAGE = 8 * 1024 * 1024      # 8 Mo
MAX_FICHIER = 50 * 1024 * 1024   # 50 Mo

EXT_IMAGE = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
EXT_FICHIER = {
    '.pdf', '.doc', '.docx', '.odt', '.ppt', '.pptx', '.xls', '.xlsx', '.csv', '.txt',
    '.mp3', '.wav', '.m4a', '.ogg', '.aac',
    '.mp4', '.webm', '.mov', '.m4v', '.avi', '.mkv',
    '.jpg', '.jpeg', '.png', '.webp', '.gif', '.zip',
}


def _valider(fichier, taille_max, extensions, quoi):
    if not fichier:
        return fichier
    if fichier.size > taille_max:
        raise ValidationError(
            "Fichier trop volumineux ({:.0f} Mo max).".format(taille_max / 1024 / 1024))
    ext = os.path.splitext(fichier.name)[1].lower()
    if ext not in extensions:
        raise ValidationError(
            "Type de {} non autorisé ({}). Extensions acceptées : {}.".format(
                quoi, ext or 'inconnu', ', '.join(sorted(extensions))))
    return fichier


def valider_image(fichier):
    return _valider(fichier, MAX_IMAGE, EXT_IMAGE, 'image')


def valider_fichier(fichier):
    return _valider(fichier, MAX_FICHIER, EXT_FICHIER, 'fichier')
