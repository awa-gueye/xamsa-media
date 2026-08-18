import os

from django.apps import AppConfig


class VeilleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veille'
    verbose_name = 'Veille et revue de presse'

    def ready(self):
        # Demarre uniquement dans le processus qui sert le site :
        # - en dev : runserver pose RUN_MAIN=true ;
        # - en prod : on pose RUN_SCHEDULER=1 pour le seul processus gunicorn
        #   (pas pour migrate/collectstatic/seed).
        if os.environ.get('RUN_MAIN') != 'true' and os.environ.get('RUN_SCHEDULER') != '1':
            return
        try:
            from veille.scheduler import demarrer_ingestion_auto
            demarrer_ingestion_auto(240)
        except Exception:
            pass
