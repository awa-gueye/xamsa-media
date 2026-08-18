# -*- coding: utf-8 -*-
"""Vues des ecrans principaux."""
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from espaces.models import ItemCommunaute, MediaSenegal, Ressource
from multimedia.models import Media
from comptes.models import Contribution
from redaction.models import Article, Categorie
from veille.models import RevueItem

POLES = {
    'Investigation': "Enquêtes de terrain et révélations documentées.",
    'Économie': "Budget, secteurs, emploi et décryptage des chiffres.",
    'Politique': "Institutions, pouvoir et vie publique.",
    'Environnement': "Littoral, climat, ressources et territoires.",
    'Science & Tech': "Numérique, innovation et recherche.",
    'Santé': "Système de soins, prévention et accès.",
    'Culture & Religion': "Arts, société et faits religieux.",
    'Sport': "Disciplines, clubs et grands rendez-vous.",
}

# Libelles des sous-onglets "Medias du Senegal".
MEDIA_TABS = [('histoire', 'Histoire des médias'), ('portrait', 'Portraits de journalistes'),
              ('tv', 'Chaînes TV'), ('radio', 'Radios'), ('presse', 'Presse écrite'),
              ('numerique', 'Médias numériques'), ('podcast', 'Podcasts')]


def home(request):
    from veille.models import Brief
    latest = list(RevueItem.objects.select_related('source').order_by('-date')[:5])
    return render(request, 'home.html', {
        'latest': latest, 'une': latest[0] if latest else None,
        'revue': RevueItem.objects.select_related('source').order_by('-date')[:3],
        'enquetes': Article.objects.filter(publie=True, type='enquete')[:3],
        'mur': RevueItem.objects.select_related('source').order_by('-date')[:14],
        'publications': Contribution.objects.filter(statut='publie').select_related('auteur')[:6],
        'brief': Brief.objects.first(),
    })


# ---------- RUBRIQUES ----------
def rubriques(request):
    cats = [{'obj': c, 'desc': POLES.get(c.nom, ''),
             'count': c.articles.filter(publie=True).count()} for c in Categorie.objects.all()]
    return render(request, 'rubriques.html', {'cats': cats})


def rubrique_detail(request, slug):
    categorie = get_object_or_404(Categorie, slug=slug)
    return render(request, 'rubrique_detail.html',
                  {'categorie': categorie, 'articles': categorie.articles.filter(publie=True),
                   'desc': POLES.get(categorie.nom, '')})


def medias_senegal(request, type_slug=None):
    qs = MediaSenegal.objects.filter(publie=True)
    if type_slug:
        qs = qs.filter(type=type_slug)
    tabs = [{'slug': None, 'label': 'Tout', 'url': reverse('medias_senegal')}]
    for slug, lbl in MEDIA_TABS:
        tabs.append({'slug': slug, 'label': lbl, 'url': reverse('medias_senegal_type', args=[slug])})
    return render(request, 'medias_senegal.html', {
        'items': qs, 'tabs': tabs, 'current': type_slug,
        'label': dict(MEDIA_TABS).get(type_slug) if type_slug else None})


# ---------- DOSSIERS ----------
def dossiers(request):
    return render(request, 'dossiers.html', {
        'nos_dossiers': Article.objects.filter(publie=True, type__in=['dossier', 'enquete'])[:6],
        'curation': RevueItem.objects.select_related('source').order_by('-date')[:8]})


def audio_video(request):
    return render(request, 'audio_video.html', {
        'docs': Media.objects.filter(publie=True, type='documentaire'),
        'podcasts': Media.objects.filter(publie=True, type='podcast')})


# ---------- ACADEMIE / COMMUNAUTE ----------
def _espace(request, template, model, types, type_slug, titre, intro, urlbase, extra=None):
    qs = model.objects.filter(publie=True)
    if type_slug:
        qs = qs.filter(type=type_slug)
    tabs = [{'slug': None, 'label': 'Tout', 'url': reverse(urlbase)}]
    for slug, lbl in types:
        tabs.append({'slug': slug, 'label': lbl, 'url': reverse(urlbase + '_type', args=[slug])})
    ctx = {'items': qs, 'tabs': tabs, 'current': type_slug, 'titre': titre, 'intro': intro,
           'label': dict(types).get(type_slug) if type_slug else None}
    if extra:
        ctx.update(extra)
    return render(request, template, ctx)


def academie(request, type_slug=None):
    return _espace(request, 'academie.html', Ressource, Ressource.TYPES, type_slug, "Académie",
                   "Se former au journalisme et à l'analyse des médias.", 'academie')


def communaute(request, type_slug=None):
    contributions = []
    if type_slug in (None, 'contribution'):
        contributions = Contribution.objects.filter(statut='publie').select_related('auteur')[:12]
    return _espace(request, 'communaute.html', ItemCommunaute, ItemCommunaute.TYPES, type_slug,
                   "Communauté", "Contribuez, participez et saisissez les opportunités.", 'communaute',
                   extra={'contributions': contributions})


# ---------- RECHERCHE ----------
def recherche(request):
    q = (request.GET.get('q') or '').strip()
    articles = revue = autres = []
    reponse_ia = None
    if q:
        # Reponse redigee facon moteur de reponse, cadree sur le journalisme.
        from assistant.engine import repondre as _repondre_ia
        try:
            reponse_ia = _repondre_ia(q)
        except Exception:  # la recherche classique reste disponible en cas d'echec.
            reponse_ia = None
        articles = Article.objects.filter(
            Q(titre__icontains=q) | Q(chapo__icontains=q) | Q(corps__icontains=q), publie=True)[:9]
        revue = RevueItem.objects.filter(
            Q(titre__icontains=q) | Q(resume__icontains=q)).select_related('source')[:9]
        autres = []
        for model, espace in ((Ressource, 'Académie'), (ItemCommunaute, 'Communauté'),
                              (MediaSenegal, 'Médias du Sénégal')):
            for o in model.objects.filter(Q(titre__icontains=q) | Q(description__icontains=q), publie=True)[:4]:
                autres.append({'titre': o.titre, 'espace': espace, 'desc': o.description, 'lien': o.lien})
    return render(request, 'recherche.html', {'q': q, 'articles': articles, 'revue': revue,
                                               'autres': autres, 'reponse_ia': reponse_ia})


def latest_json(request):
    from django.http import JsonResponse
    items = []
    for it in RevueItem.objects.select_related('source').order_by('-date')[:14]:
        items.append({
            'titre': it.titre_propre, 'source': it.source.nom, 'url': it.url,
            'time': it.date.strftime('%H:%M'), 'datetime': it.date.strftime('%d/%m %H:%M'),
            'image': it.image_url or '',
        })
    return JsonResponse({'items': items})
