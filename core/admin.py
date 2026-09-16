# -*- coding: utf-8 -*-
import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import AbonneNewsletter


@admin.action(description='Exporter en CSV')
def exporter_abonnes_csv(modeladmin, request, queryset):
    resp = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    resp['Content-Disposition'] = 'attachment; filename="abonnes_newsletter.csv"'
    resp.write('﻿')  # BOM : accents corrects dans Excel
    w = csv.writer(resp)
    w.writerow(['Email', 'Actif', 'Inscrit le'])
    for a in queryset:
        w.writerow([a.email, 'Oui' if a.actif else 'Non',
                    a.date.strftime('%Y-%m-%d %H:%M') if a.date else ''])
    return resp


@admin.register(AbonneNewsletter)
class AbonneNewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'actif', 'date')
    list_filter = ('actif', 'date')
    search_fields = ('email',)
    list_editable = ('actif',)
    actions = [exporter_abonnes_csv]
