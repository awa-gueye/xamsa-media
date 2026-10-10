# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Article, ArticleCommentaire, ArticleJaime


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, publie=True)
    commentaires = (article.commentaires.filter(masque=False, parent__isnull=True)
                    .select_related('auteur', 'auteur__profil')
                    .prefetch_related('reponses__auteur__profil'))
    nb_commentaires = article.commentaires.filter(masque=False).count()
    nb_jaime = article.jaimes.count()
    a_aime = request.user.is_authenticated and article.jaimes.filter(auteur=request.user).exists()
    return render(request, 'article_detail.html', {
        'article': article, 'commentaires': commentaires,
        'nb_commentaires': nb_commentaires, 'nb_jaime': nb_jaime, 'a_aime': a_aime})


@login_required
@require_POST
def article_jaime(request, slug):
    article = get_object_or_404(Article, slug=slug, publie=True)
    jaime = article.jaimes.filter(auteur=request.user).first()
    if jaime:
        jaime.delete()
        a_aime = False
    else:
        ArticleJaime.objects.create(article=article, auteur=request.user)
        a_aime = True
    return JsonResponse({'a_aime': a_aime, 'total': article.jaimes.count()})


@login_required
@require_POST
def article_commenter(request, slug):
    article = get_object_or_404(Article, slug=slug, publie=True)
    texte = (request.POST.get('texte') or '').strip()
    parent = None
    parent_id = request.POST.get('parent')
    if parent_id:
        parent = ArticleCommentaire.objects.filter(
            pk=parent_id, article=article, parent__isnull=True).first()

    # Anti-spam : 1 commentaire / 15 s, 15 / heure.
    maintenant = timezone.now()
    if request.user.commentaires_articles.filter(date__gte=maintenant - timedelta(seconds=15)).exists():
        messages.error(request, "Vous commentez trop vite. Patientez quelques secondes.")
        return redirect(article.get_absolute_url() + '#commentaires')
    if request.user.commentaires_articles.filter(date__gte=maintenant - timedelta(hours=1)).count() >= 15:
        messages.error(request, "Vous avez atteint la limite de commentaires. Réessayez plus tard.")
        return redirect(article.get_absolute_url() + '#commentaires')

    if texte:
        ArticleCommentaire.objects.create(article=article, auteur=request.user,
                                          texte=texte[:3000], parent=parent)
    else:
        messages.error(request, 'Votre commentaire est vide.')
    return redirect(article.get_absolute_url() + '#commentaires')


@login_required
@require_POST
def article_supprimer_commentaire(request, pk):
    comm = get_object_or_404(ArticleCommentaire, pk=pk)
    if comm.auteur_id == request.user.id or request.user.is_superuser:
        article_url = comm.article.get_absolute_url()
        comm.delete()
        return redirect(article_url + '#commentaires')
    messages.error(request, "Action non autorisée.")
    return redirect('home')
