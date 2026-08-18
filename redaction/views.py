from django.shortcuts import get_object_or_404, render

from .models import Article


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, publie=True)
    return render(request, 'article_detail.html', {'article': article})
