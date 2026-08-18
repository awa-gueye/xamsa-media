from django.contrib import admin

from .models import Article, Categorie


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug')
    prepopulated_fields = {'slug': ('nom',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'categorie', 'a_la_une', 'publie', 'date_publication')
    list_filter = ('type', 'categorie', 'a_la_une', 'publie')
    search_fields = ('titre', 'chapo', 'corps')
    prepopulated_fields = {'slug': ('titre',)}
    list_editable = ('a_la_une', 'publie')
    date_hierarchy = 'date_publication'
