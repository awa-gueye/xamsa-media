from django.contrib import admin

from .models import Brief, RevueItem, Source


@admin.register(Brief)
class BriefAdmin(admin.ModelAdmin):
    list_display = ('date', 'date_generation')


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'actif', 'url_rss')
    list_filter = ('categorie', 'actif')
    list_editable = ('actif',)


@admin.register(RevueItem)
class RevueItemAdmin(admin.ModelAdmin):
    list_display = ('titre', 'source', 'date')
    list_filter = ('source',)
    search_fields = ('titre', 'resume')
    date_hierarchy = 'date'
