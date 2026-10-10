from django.contrib import admin

from .models import Article, ArticleCommentaire, ArticleJaime, Categorie


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug', 'image_url')
    prepopulated_fields = {'slug': ('nom',)}


@admin.action(description='Masquer les commentaires sélectionnés')
def masquer_comm_articles(modeladmin, request, queryset):
    queryset.update(masque=True)


@admin.register(ArticleCommentaire)
class ArticleCommentaireAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'article', 'parent', 'masque', 'date')
    list_filter = ('masque', 'date')
    search_fields = ('texte', 'auteur__username', 'article__titre')
    list_editable = ('masque',)
    actions = [masquer_comm_articles]


@admin.register(ArticleJaime)
class ArticleJaimeAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'article', 'date')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'categorie', 'a_la_une', 'derniere_minute', 'publie', 'date_publication')
    list_filter = ('type', 'categorie', 'a_la_une', 'derniere_minute', 'publie')
    search_fields = ('titre', 'chapo', 'corps')
    prepopulated_fields = {'slug': ('titre',)}
    list_editable = ('a_la_une', 'derniere_minute', 'publie')
    date_hierarchy = 'date_publication'
