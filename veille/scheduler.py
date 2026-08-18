# -*- coding: utf-8 -*-
"""Ingestion automatique en arriere-plan (thread) pendant que le serveur tourne.

Evite d'avoir a lancer 'ingest' a la main : l'actualite se rafraichit toute seule.
"""
import logging
import threading
import time

_lock = threading.Lock()
_started = False
_log = logging.getLogger('xamsa')


def _boucle(intervalle):
    time.sleep(8)  # laisser le serveur finir de demarrer
    from django.core.management import call_command
    from django.db import connections
    while True:
        try:
            call_command('ingest', '--limit', '25', verbosity=0)
            # Genere le brief du jour une fois (retourne l'existant les fois suivantes).
            from assistant.brief import generer_brief_du_jour
            generer_brief_du_jour()
        except Exception as e:
            _log.warning('ingest auto: %s', e)
        finally:
            for conn in connections.all():
                conn.close()
        time.sleep(intervalle)


def demarrer_ingestion_auto(intervalle=240):
    """Demarre la boucle une seule fois (intervalle en secondes, defaut 4 min)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_boucle, args=(intervalle,), daemon=True).start()
