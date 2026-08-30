import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import Commentaire, Contribution, Notification, Profil, Reaction


@admin.action(description='Exporter en CSV (pour analyse)')
def exporter_utilisateurs_csv(modeladmin, request, queryset):
    """Télécharge les profils sélectionnés (ou tous) en CSV, encodage Excel-compatible."""
    resp = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    resp['Content-Disposition'] = 'attachment; filename="utilisateurs_xamsa.csv"'
    resp.write('﻿')  # BOM : accents corrects dans Excel
    w = csv.writer(resp)
    w.writerow(['Prénom', 'Nom', 'Email', 'Profil', 'Téléphone', 'Localisation',
                'Organisation', 'De confiance', 'Date inscription', 'Dernière connexion'])
    for p in queryset.select_related('user'):
        u = p.user
        w.writerow([
            u.first_name, u.last_name, u.email, p.get_type_profil_display(),
            p.telephone, p.localisation, p.organisation,
            'Oui' if p.de_confiance else 'Non',
            p.date_inscription.strftime('%Y-%m-%d %H:%M') if p.date_inscription else '',
            u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else '',
        ])
    return resp


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'type_profil', 'de_confiance', 'localisation', 'date_inscription')
    list_filter = ('type_profil', 'de_confiance')
    list_editable = ('de_confiance',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'organisation')
    actions = [exporter_utilisateurs_csv]


@admin.action(description='Marquer comme publié')
def publier_contributions(modeladmin, request, queryset):
    queryset.update(statut='publie')


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'destination', 'auteur', 'statut', 'moderation_verdict', 'moderation_score', 'date')
    list_filter = ('statut', 'type', 'destination', 'moderation_verdict')
    search_fields = ('titre', 'resume', 'corps', 'auteur__username')
    list_editable = ('statut',)
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
