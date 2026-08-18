from django.contrib import admin

from .models import Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'duree', 'publie', 'date_publication')
    list_filter = ('type', 'publie')
    search_fields = ('titre', 'description')
    list_editable = ('publie',)
