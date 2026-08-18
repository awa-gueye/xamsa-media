from django.contrib import admin

from .models import ItemCommunaute, MediaSenegal, Ressource


@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'meta', 'publie', 'date')
    list_filter = ('type', 'publie')
    search_fields = ('titre', 'description')


@admin.register(ItemCommunaute)
class ItemCommunauteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'meta', 'publie', 'date')
    list_filter = ('type', 'publie')
    search_fields = ('titre', 'description')


@admin.register(MediaSenegal)
class MediaSenegalAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'meta', 'publie', 'date')
    list_filter = ('type', 'publie')
    search_fields = ('titre', 'description')
