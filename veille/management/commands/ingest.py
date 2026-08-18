# -*- coding: utf-8 -*-
"""Collecte les flux RSS.

Image de chaque item :
  1) image REELLE de l'article fournie par le flux (affichee directement,
     comme le fait le navigateur : c'est la methode qui marchait au depart) ;
  2) sinon og:image de la page (sauf agregateurs a logo : AllAfrica, Google) ;
  3) sinon une illustration thematique locale selon le sujet.
"""
import re
from datetime import datetime, timezone as dt_timezone
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from django.core.management.base import BaseCommand
from django.templatetags.static import static

from veille.models import RevueItem, Source
from veille.text_utils import nettoyer_texte

_IMG = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
_OG = re.compile(r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]*content=["\']([^"\']+)', re.I)
_OG2 = re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']og:image', re.I)
_UA = 'Mozilla/5.0 (compatible; XamsaMediaBot/1.0; +https://xamsa.media)'
_SKIP_OG = ('allafrica.com', 'news.google.com', 'google.com', 'adakar.com')
_LOGO_HINT = re.compile(r'logo|placeholder|default|sprite|favicon|apple-touch|/share|og-default|blank', re.I)

_CATS = [
    ('justice', re.compile(r'justice|tribunal|proc[eè]s|arrestation|polici|gendarmerie|prison|condamn|\bjuge\b|commissariat|meurtre|interpell|s[ée]curisation|trafic|drogue|d[ée]tenu|inculp', re.I)),
    ('sport', re.compile(r'football|\bfoot\b|lions|\bmatch\b|\bcoupe\b|joueur|[ée]quipe nationale|basket|lutte|\bstade\b|\bsport|\bcan\b|mondial|champion|s[ée]lection', re.I)),
    ('sante', re.compile(r'sant[ée]|h[oô]pital|maladie|m[ée]decin|covid|vaccin|patient|[ée]pid[ée]mie|paludisme|dialyse|soins', re.I)),
    ('tech', re.compile(r'num[ée]rique|technologie|internet|cyber|\bapplication\b|startup|digital|hacker|intelligence artificielle|t[ée]l[ée]com|\bdata\b', re.I)),
    ('environnement', re.compile(r'environnement|climat|littoral|\bp[eê]che\b|inondation|d[ée]chet|for[eê]t|pollution|agricultur|[ée]rosion|s[ée]cheresse', re.I)),
    ('economie', re.compile(r'[ée]conomie|\bfranc\b|\bcfa\b|bceao|budget|march[ée]|entreprise|banque|monnaie|\b[ée]co\b|croissance|inflation|investiss|\bemploi\b|uemoa|financ|commerce|\bprix\b|import|export|p[ée]trole|\bgaz\b|recettes|paiement', re.I)),
    ('culture', re.compile(r'culture|musique|\bart\b|festival|cin[ée]ma|\bfilm\b|magal|gamou|religieu|mosqu[ée]e|touba|cheikh|khalife|tabaski|korit[ée]|serigne|artiste|patrimoine', re.I)),
    ('politique', re.compile(r'politiqu|ministre|pr[ée]siden|assembl[ée]e|[ée]lection|pastef|gouvernement|\bparti\b|sonko|diomaye|macky|\b[ée]tat\b|d[ée]put[ée]|\bmaire\b|diploma|\bonu\b|cedeao|c[ée]d[ée]ao|nations unies', re.I)),
    ('societe', re.compile(r'soci[ée]t[ée]|[ée]ducation|[ée]cole|universit[ée]|\bfemme|\bjeune|social|gr[eè]ve|manifestation|accident|transport|\broute\b|religion|migration', re.I)),
]


def _categorie(txt):
    for nom, rx in _CATS:
        if rx.search(txt):
            return nom
    return 'general'


def _illustration(txt):
    return static('img/cat/{}.svg'.format(_categorie(txt)))


def _date_entree(entry):
    for champ in ('published_parsed', 'updated_parsed'):
        v = getattr(entry, champ, None) or entry.get(champ)
        if v:
            return datetime(*v[:6], tzinfo=dt_timezone.utc)
    return datetime.now(dt_timezone.utc)


def _image_rss(entry):
    med = entry.get('media_content')
    if med and isinstance(med, list):
        best = max(med, key=lambda m: int(m.get('width') or 0))
        if best.get('url'):
            return best['url']
    for coll in (entry.get('enclosures', []), entry.get('links', [])):
        for it in coll or []:
            if str(it.get('type', '')).startswith('image') and (it.get('href') or it.get('url')):
                return it.get('href') or it.get('url')
    contenu = ''
    if entry.get('content'):
        contenu = entry['content'][0].get('value', '')
    contenu = contenu or entry.get('summary', '')
    m = _IMG.search(contenu or '')
    if m:
        return m.group(1)
    thumb = entry.get('media_thumbnail')
    if thumb and isinstance(thumb, list) and thumb[0].get('url'):
        return thumb[0]['url']
    return ''


def _og_image(url):
    dom = urlparse(url).netloc.lower()
    if any(d in dom for d in _SKIP_OG):
        return ''
    try:
        r = requests.get(url, headers={'User-Agent': _UA}, timeout=6)
        m = _OG.search(r.text) or _OG2.search(r.text)
        if m:
            u = urljoin(url, m.group(1).strip())
            if u.startswith('http') and not _LOGO_HINT.search(u):
                return u
    except Exception:
        pass
    return ''


class Command(BaseCommand):
    help = 'Recupere les flux RSS ; textes nettoyes, image reelle de l article (ou illustration).'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=25)

    def handle(self, *args, **options):
        limite = options['limit']
        total = maj = 0
        og_budget = 55
        for source in Source.objects.filter(actif=True):
            flux = feedparser.parse(source.url_rss, agent=_UA)
            entries = getattr(flux, 'entries', [])
            if not entries:
                self.stderr.write('  ! Aucun item : {}'.format(source.nom))
                continue
            for entry in entries[:limite]:
                lien = entry.get('link', '')
                titre = nettoyer_texte(entry.get('title', ''))
                if not lien or not titre:
                    continue
                resume = nettoyer_texte(entry.get('summary', ''))[:600]
                existe = RevueItem.objects.filter(source=source, url=lien).first()
                existant = existe.image_url if existe else ''
                if existant.startswith('http'):
                    image = existant  # vraie image distante deja en place : on garde
                else:
                    rss = _image_rss(entry)
                    og = ''
                    if og_budget > 0:
                        og = _og_image(lien)  # haute resolution (ignore pour les agregateurs)
                        og_budget -= 1
                    image = og or rss or _illustration(titre + ' ' + resume)

                if existe is None:
                    RevueItem.objects.create(source=source, url=lien, titre=titre[:400],
                                             resume=resume, image_url=image, date=_date_entree(entry))
                    total += 1
                else:
                    champs = {}
                    if existe.titre != titre[:400]:
                        champs['titre'] = titre[:400]
                    if not existe.resume and resume:
                        champs['resume'] = resume
                    if image and existe.image_url != image:
                        champs['image_url'] = image
                    if champs:
                        for k, v in champs.items():
                            setattr(existe, k, v)
                        existe.save(update_fields=list(champs))
                        maj += 1
            self.stdout.write('  {} : {} items'.format(source.nom, len(entries)))
        self.stdout.write(self.style.SUCCESS('{} ajoutes, {} mis a jour.'.format(total, maj)))
