# -*- coding: utf-8 -*-
"""Assainissement du HTML soumis par les utilisateurs (editeur enrichi).

On conserve une liste blanche de balises de mise en forme et on retire tout le
reste : scripts, styles, iframes, gestionnaires d'evenements (onclick...),
liens javascript:. Objectif : empecher toute injection (XSS stocke) tout en
gardant un article lisible. Aucune dependance externe.
"""
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

# Balises de mise en forme conservees.
BALISES_AUTORISEES = {
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'h2', 'h3', 'h4',
    'ul', 'ol', 'li', 'blockquote', 'a', 'hr', 'div',
}
# Balises sans contenu (auto-fermantes).
BALISES_VIDES = {'br', 'hr'}
# Normalisation : div (produit par contenteditable) devient un paragraphe.
REMAP = {'div': 'p'}
# Attributs autorises, par balise.
ATTRS_AUTORISES = {'a': {'href', 'title'}}
# Schemas d'URL surs pour href ('' = lien relatif).
SCHEMAS_OK = {'http', 'https', 'mailto', ''}
# Balises dont on jette aussi le contenu (jamais affiche).
CONTENU_IGNORE = {'script', 'style', 'noscript', 'iframe', 'object', 'embed',
                  'template', 'svg', 'math', 'title', 'textarea'}


class _Nettoyeur(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sortie = []
        self.pile = []
        self.ignore = 0  # profondeur dans une balise a contenu ignore

    def handle_starttag(self, tag, attrs):
        if self.ignore:
            if tag in CONTENU_IGNORE:
                self.ignore += 1
            return
        if tag in CONTENU_IGNORE:
            self.ignore += 1
            return
        if tag not in BALISES_AUTORISEES:
            return  # balise inconnue : on la retire mais on garde son texte
        attrs_rendu = self._attrs(tag, attrs)
        sortie_tag = REMAP.get(tag, tag)
        if tag in BALISES_VIDES:
            self.sortie.append('<{}>'.format(sortie_tag))
        else:
            self.pile.append(sortie_tag)
            self.sortie.append('<{}{}>'.format(sortie_tag, attrs_rendu))

    def handle_startendtag(self, tag, attrs):
        if self.ignore or tag not in BALISES_AUTORISEES:
            return
        sortie_tag = REMAP.get(tag, tag)
        self.sortie.append('<{}{}>'.format(sortie_tag, self._attrs(tag, attrs)))

    def handle_endtag(self, tag):
        if self.ignore:
            if tag in CONTENU_IGNORE:
                self.ignore -= 1
            return
        if tag not in BALISES_AUTORISEES or tag in BALISES_VIDES:
            return
        sortie_tag = REMAP.get(tag, tag)
        if sortie_tag in self.pile:
            while self.pile:
                ouverte = self.pile.pop()
                self.sortie.append('</{}>'.format(ouverte))
                if ouverte == sortie_tag:
                    break

    def handle_data(self, data):
        if self.ignore:
            return
        self.sortie.append(escape(data))

    def _attrs(self, tag, attrs):
        permis = ATTRS_AUTORISES.get(tag, set())
        morceaux, href_emis = [], False
        for nom, val in attrs:
            nom = (nom or '').lower()
            if nom not in permis:
                continue
            val = val or ''
            if nom == 'href':
                if not self._href_ok(val):
                    continue
                href_emis = True
            morceaux.append('{}="{}"'.format(nom, escape(val, quote=True)))
        rendu = ''.join(' ' + m for m in morceaux)
        if tag == 'a' and href_emis:  # lien externe : navigation sure
            rendu += ' rel="noopener noreferrer" target="_blank"'
        return rendu

    def _href_ok(self, val):
        try:
            return urlparse(val.strip()).scheme.lower() in SCHEMAS_OK
        except ValueError:
            return False

    def resultat(self):
        while self.pile:
            self.sortie.append('</{}>'.format(self.pile.pop()))
        return ''.join(self.sortie)


def nettoyer_html(html):
    """Retourne une version sure du HTML (chaine simple, non marquee safe)."""
    if not html:
        return ''
    n = _Nettoyeur()
    n.feed(html)
    n.close()
    return n.resultat().strip()
