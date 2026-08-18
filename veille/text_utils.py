# -*- coding: utf-8 -*-
"""Nettoyage du texte issu des flux (decodage des entites, suppression des balises)."""
import html
import re

_TAGS = re.compile(r'<[^>]+>')
_WS = re.compile(r'\s+')


def nettoyer_texte(t):
    if not t:
        return ''
    t = _TAGS.sub(' ', t)          # enlever les balises HTML
    prev = None
    while t != prev:               # decoder les entites, meme double-encodees (&#xe9; -> é)
        prev = t
        t = html.unescape(t)
    return _WS.sub(' ', t).strip()  # normaliser les espaces
