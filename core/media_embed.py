# -*- coding: utf-8 -*-
"""Aide au rendu des videos (YouTube) : extraction de l'ID et URL d'integration."""
import re

_YT = re.compile(
    r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/|v/|live/))([\w-]{11})'
)


def youtube_id(url):
    """Renvoie l'identifiant de la video YouTube contenu dans l'URL, ou ''."""
    if not url:
        return ''
    m = _YT.search(url)
    return m.group(1) if m else ''


def youtube_embed(url):
    """URL d'integration (iframe) pour une video YouTube, ou '' si non reconnue."""
    vid = youtube_id(url)
    return 'https://www.youtube.com/embed/{}'.format(vid) if vid else ''
