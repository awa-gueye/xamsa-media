from django.contrib import admin

from .models import Commentaire, Contribution, Notification, Profil, Reaction


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'type_profil', 'de_confiance', 'localisation', 'date_inscription')
    list_filter = ('type_profil', 'de_confiance')
    list_editable = ('de_confiance',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'organisation')


@admin.action(description='Marquer comme publié')
def publier_contributions(modeladmin, request, queryset):
    queryset.update(statut='publie')


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'auteur', 'statut', 'moderation_verdict', 'moderation_score', 'date')
    list_filter = ('statut', 'type', 'moderation_verdict')
    search_fields = ('titre', 'resume', 'corps', 'auteur__username')
    actions = [publier_contributions]


@admin.action(description='Masquer les commentaires sélectionnés')
def masquer_commentaires(modeladmin, request, queryset):
    queryset.update(masque=True)


@admin.action(description='Afficher les commentaires sélectionnés')
def afficher_commentaires(modeladmin, request, queryset):
    queryset.update(masque=False)


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'contribution', 'parent', 'masque', 'date')
    list_filter = ('masque', 'date')
    search_fields = ('texte', 'auteur__username', 'contribution__titre')
    actions = [masquer_commentaires, afficher_commentaires]


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'contribution', 'type', 'date')
    list_filter = ('type',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'acteur', 'type', 'contribution', 'lu', 'date')
    list_filter = ('type', 'lu')
