from django.contrib import admin

from .models import Bibliotheque, Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'duree', 'publie', 'date_publication')
    list_filter = ('type', 'publie')
    search_fields = ('titre', 'description')
    list_editable = ('publie',)


@admin.register(Bibliotheque)
class BibliothequeAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'date')
    list_filter = ('type', 'date')
    search_fields = ('titre', 'description')
    date_hierarchy = 'date'
