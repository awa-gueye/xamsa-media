from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path('inscription/', views.inscription, name='inscription'),
    path('inscription/verification/', views.verifier_email, name='verifier_email'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    # Reinitialisation du mot de passe (vues Django, templates maison).
    path('mot-de-passe/', auth_views.PasswordResetView.as_view(
        template_name='comptes/pwd_reset.html',
        email_template_name='comptes/pwd_reset_email.txt',
        subject_template_name='comptes/pwd_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')), name='password_reset'),
    path('mot-de-passe/envoye/', auth_views.PasswordResetDoneView.as_view(
        template_name='comptes/pwd_reset_done.html'), name='password_reset_done'),
    path('reinitialiser/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='comptes/pwd_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')), name='password_reset_confirm'),
    path('reinitialiser/termine/', auth_views.PasswordResetCompleteView.as_view(
        template_name='comptes/pwd_reset_complete.html'), name='password_reset_complete'),
    path('mon-compte/', views.compte, name='compte'),
    path('mon-compte/modifier/', views.modifier_profil, name='modifier_profil'),
    path('notifications/', views.notifications, name='notifications'),
    path('moderation/', views.moderation, name='moderation'),
    path('moderation/<int:pk>/', views.moderer, name='moderer'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
    path('publication/<int:pk>/favori/', views.favori, name='favori'),
    path('auteur/<int:user_id>/', views.profil_public, name='profil_public'),
    path('publier/', views.publier, name='publier'),
    path('publication/<int:pk>/', views.publication_detail, name='publication_detail'),
    path('publication/<int:pk>/modifier/', views.contribution_modifier, name='contribution_modifier'),
    path('publication/<int:pk>/supprimer/', views.contribution_supprimer, name='contribution_supprimer'),
    path('publication/<int:pk>/fichier/', views.telecharger_fichier, name='telecharger_fichier'),
    path('publication/<int:pk>/commenter/', views.commenter, name='commenter'),
    path('publication/<int:pk>/reagir/', views.reagir, name='reagir'),
    path('commentaire/<int:pk>/supprimer/', views.supprimer_commentaire, name='supprimer_commentaire'),
]
