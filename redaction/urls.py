from django.urls import path

from . import views

urlpatterns = [
    path('<slug:slug>/commenter/', views.article_commenter, name='article_commenter'),
    path('<slug:slug>/jaime/', views.article_jaime, name='article_jaime'),
    path('commentaire/<int:pk>/supprimer/', views.article_supprimer_commentaire,
         name='article_supprimer_commentaire'),
    path('<slug:slug>/', views.article_detail, name='article_detail'),
]
