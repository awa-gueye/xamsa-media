# -*- coding: utf-8 -*-
"""Retire définitivement SeneNews de « Médias du Sénégal », y compris en prod
(cette migration s'exécute au déploiement via `migrate`)."""
from django.db import migrations


def supprimer_senenews(apps, schema_editor):
    MediaSenegal = apps.get_model('espaces', 'MediaSenegal')
    MediaSenegal.objects.filter(titre__iexact='SeneNews').delete()
    MediaSenegal.objects.filter(titre__icontains='senenews').delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('espaces', '0002_itemcommunaute_logo_mediasenegal_logo_ressource_logo'),
    ]
    operations = [
        migrations.RunPython(supprimer_senenews, noop),
    ]
