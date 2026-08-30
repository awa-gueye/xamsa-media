# -*- coding: utf-8 -*-
"""Endpoint du chatbot "Looy laaj ?".

Assistant conversationnel (RAG) : classification du message, recuperation de
contexte utile (contenu du site + web), redaction par un LLM (Gemini par defaut),
et sources citees uniquement quand c'est necessaire. Toute la logique est dans
`assistant/engine.py` (partagee avec la page de recherche).
"""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .engine import repondre


@csrf_exempt  # Prototype. En production : gerer le jeton CSRF cote client.
@require_POST
def ask(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}
    question = (data.get('question') or '').strip()
    if not question:
        return JsonResponse({'texte': "Posez-moi une question.", 'sources': []})

    # Historique de conversation optionnel : liste de {role: 'user'|'bot', texte}.
    historique = data.get('historique')
    if not isinstance(historique, list):
        historique = None

    # Intention choisie par l'utilisateur : rechercher / retrouver / comparer / expliquer.
    mode = (data.get('mode') or '').strip().lower()
    if mode not in ('rechercher', 'retrouver', 'comparer', 'expliquer'):
        mode = None

    # Looy laaj cite ses sources (titre, date, lien) et un niveau de confiance.
    return JsonResponse(repondre(question, historique=historique, mode=mode,
                                 avec_web=True, avec_sources=True))
