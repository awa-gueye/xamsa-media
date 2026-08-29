# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ConnexionForm, ContributionForm, InscriptionForm
from .models import Commentaire, Contribution, Favori, Notification, Profil, Reaction

ROLES = [
    ('lecteur', "Lecteur / Citoyen", "Suivez l'actualité, commentez et proposez des sujets."),
    ('journaliste', "Journaliste / Contributeur", "Proposez et publiez des contenus, participez aux enquêtes."),
    ('etudiant', "Étudiant de l'Académie", "Accédez aux cours, formations et certifications."),
    ('organe', "Organe de presse / Association", "Rédaction, syndicat ou association de presse."),
]


def _envoyer_code_email(email, prenom, code):
    from django.conf import settings
    from django.core.mail import send_mail
    send_mail(
        'Votre code de vérification Xamsa Média',
        ('Bonjour {},\n\nVotre code de vérification est : {}\n\n'
         'Saisissez-le sur Xamsa Média pour finaliser votre inscription. '
         'Il est valable 20 minutes.\n\n'
         "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n\n"
         "L'équipe Xamsa Média").format(prenom, code),
        settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)


def inscription(request):
    from django.conf import settings
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = InscriptionForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            # Sans email configure : inscription directe (on ne bloque personne).
            if not getattr(settings, 'EMAIL_ACTIF', False):
                user = form.save()
                login(request, user)
                messages.success(request, 'Votre compte a été créé. Bienvenue sur Xamsa Média !')
                return redirect('home')

            # Avec email : on n'enregistre PAS encore ; on envoie un code a 6 chiffres.
            import random
            from datetime import timedelta

            from django.contrib.auth.hashers import make_password
            from django.core.files.storage import default_storage
            from django.utils import timezone
            photo_nom = ''
            if d.get('photo'):
                photo_nom = default_storage.save('profils/' + d['photo'].name, d['photo'])
            code = '{:06d}'.format(random.randint(0, 999999))
            request.session['inscription'] = {
                'prenom': d['prenom'], 'nom': d['nom'], 'email': d['email'],
                'type_profil': d['type_profil'], 'telephone': d.get('telephone', ''),
                'localisation': d.get('localisation', ''), 'organisation': d.get('organisation', ''),
                'photo': photo_nom, 'password': make_password(d['mot_de_passe']),
                'code': code, 'expire': (timezone.now() + timedelta(minutes=20)).isoformat(),
                'essais': 0,
            }
            try:
                _envoyer_code_email(d['email'], d['prenom'], code)
            except Exception:
                messages.error(request, "L'envoi du code a échoué. Réessayez dans un moment.")
                return render(request, 'comptes/inscription.html', {'form': form, 'roles': ROLES})
            return redirect('verifier_email')
    else:
        form = InscriptionForm()
    return render(request, 'comptes/inscription.html', {'form': form, 'roles': ROLES})


def verifier_email(request):
    """Saisie du code a 6 chiffres recu par email pour finaliser l'inscription."""
    from datetime import datetime, timedelta

    from django.utils import timezone
    pend = request.session.get('inscription')
    if not pend:
        return redirect('inscription')
    erreur = None
    if request.method == 'POST':
        if request.POST.get('renvoyer'):
            import random
            code = '{:06d}'.format(random.randint(0, 999999))
            pend['code'] = code
            pend['expire'] = (timezone.now() + timedelta(minutes=20)).isoformat()
            pend['essais'] = 0
            request.session.modified = True
            try:
                _envoyer_code_email(pend['email'], pend['prenom'], code)
                messages.success(request, 'Un nouveau code vous a été envoyé.')
            except Exception:
                messages.error(request, "L'envoi a échoué. Réessayez.")
            return redirect('verifier_email')

        saisie = (request.POST.get('code') or '').strip()
        if timezone.now() > datetime.fromisoformat(pend['expire']):
            erreur = 'Le code a expiré. Demandez-en un nouveau.'
        elif saisie != pend['code']:
            pend['essais'] = pend.get('essais', 0) + 1
            request.session.modified = True
            if pend['essais'] >= 5:
                del request.session['inscription']
                messages.error(request, 'Trop de tentatives. Reprenez votre inscription.')
                return redirect('inscription')
            erreur = 'Code incorrect. Réessayez.'
        else:
            user = User(username=pend['email'], email=pend['email'],
                        first_name=pend['prenom'], last_name=pend['nom'])
            user.password = pend['password']  # deja hache
            user.save()
            Profil.objects.create(
                user=user, type_profil=pend['type_profil'], telephone=pend['telephone'],
                localisation=pend['localisation'], organisation=pend['organisation'],
                photo=pend['photo'] or None)
            del request.session['inscription']
            login(request, user)
            messages.success(request, 'Votre compte est validé. Bienvenue sur Xamsa Média !')
            return redirect('home')
    return render(request, 'comptes/verifier_email.html', {'email': pend['email'], 'erreur': erreur})


def connexion(request):
    if request.user.is_authenticated:
        return redirect('home')
    erreur = None
    form = ConnexionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].lower()
        # retrouver le compte par email (username peut differer, ex. administrateur)
        u = User.objects.filter(email__iexact=email).first() or User.objects.filter(username__iexact=email).first()
        identifiant = u.username if u else email
        user = authenticate(request, username=identifiant, password=form.cleaned_data['mot_de_passe'])
        if user:
            login(request, user)
            return redirect(request.GET.get('next') or 'home')
        erreur = 'Email ou mot de passe incorrect.'
    return render(request, 'comptes/connexion.html', {'form': form, 'erreur': erreur})


def deconnexion(request):
    logout(request)
    return redirect('home')


@login_required
def compte(request):
    # Tout utilisateur (y compris l'administrateur) dispose d'un profil.
    profil, _ = Profil.objects.get_or_create(user=request.user)
    if request.method == 'POST' and request.FILES.get('photo'):
        profil.photo = request.FILES['photo']
        profil.save()
        messages.success(request, 'Photo de profil mise à jour.')
        return redirect('compte')
    contributions = request.user.contributions.all()
    return render(request, 'comptes/compte.html', {'profil': profil, 'contributions': contributions})


@login_required
def modifier_profil(request):
    """L'utilisateur modifie ses informations (nom, profil, coordonnées, photo)."""
    from .forms import ProfilForm
    profil, _ = Profil.objects.get_or_create(user=request.user)
    form = ProfilForm(request.POST or None, request.FILES or None, instance=profil)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vos informations ont été mises à jour.')
        return redirect('compte')
    return render(request, 'comptes/modifier_profil.html', {'form': form, 'profil': profil})


def profil_public(request, user_id):
    """Profil public d'un contributeur : photo, bio et publications, visible par tous."""
    from django.shortcuts import get_object_or_404
    auteur = get_object_or_404(User, pk=user_id)
    profil = getattr(auteur, 'profil', None)
    publications = auteur.contributions.filter(statut='publie')
    return render(request, 'comptes/profil_public.html',
                  {'auteur': auteur, 'profil': profil, 'publications': publications})


@login_required
def publier(request):
    profil = getattr(request.user, 'profil', None)
    ptype = profil.type_profil if profil else 'lecteur'
    autorises = Contribution.TYPES_PAR_PROFIL.get(ptype, ['sujet'])
    form = ContributionForm(autorises, request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        contrib = form.save(commit=False)
        contrib.auteur = request.user
        contrib.save()
        # Pré-modération IA (semi-automatique) : publie, rejette ou met en attente.
        from assistant.moderation import appliquer_moderation
        de_confiance = bool(profil and profil.de_confiance)
        try:
            appliquer_moderation(contrib, de_confiance=de_confiance)
        except Exception:
            pass  # en cas de souci, la contribution reste en attente (file humaine)
        if contrib.statut == 'publie':
            messages.success(request, "Votre contribution a été publiée. Merci pour votre participation !")
        elif contrib.statut == 'refuse':
            messages.warning(request, "Votre contribution n'a pas pu être acceptée (hors sujet ou non conforme). Vous pouvez la modifier et la resoumettre.")
        else:
            messages.success(request, "Votre contribution a été soumise. La rédaction l'examinera avant publication.")
        return redirect('compte')
    return render(request, 'comptes/publier.html', {'form': form, 'ptype': ptype, 'profil': profil})


def publication_detail(request, pk):
    from django.shortcuts import get_object_or_404
    pub = get_object_or_404(Contribution, pk=pk, statut='publie')

    # Compteur de vues : une seule par session et par publication (anti-rafraichissement).
    vues_session = request.session.get('pubs_vues', [])
    if pk not in vues_session:
        Contribution.objects.filter(pk=pk).update(vues=models.F('vues') + 1)
        pub.vues += 1
        vues_session.append(pk)
        request.session['pubs_vues'] = vues_session

    a_favori = request.user.is_authenticated and pub.favoris.filter(user=request.user).exists()
    connexes = Contribution.objects.filter(statut='publie').exclude(pk=pk).select_related('auteur')[:3]
    # Commentaires racine visibles (les reponses sont chargees via la relation).
    commentaires = pub.commentaires.filter(masque=False, parent__isnull=True) \
        .select_related('auteur', 'auteur__profil').prefetch_related('reponses__auteur__profil')
    nb_commentaires = pub.commentaires.filter(masque=False).count()
    nb_jaime = pub.reactions.count()
    a_aime = request.user.is_authenticated and pub.reactions.filter(auteur=request.user).exists()
    return render(request, 'comptes/publication_detail.html', {
        'pub': pub, 'connexes': connexes, 'commentaires': commentaires,
        'nb_commentaires': nb_commentaires, 'nb_jaime': nb_jaime, 'a_aime': a_aime,
        'a_favori': a_favori})


@login_required
@require_POST
def commenter(request, pk):
    """Ajoute un commentaire (ou une reponse) a une publication. Texte echappe."""
    from django.shortcuts import get_object_or_404
    pub = get_object_or_404(Contribution, pk=pk, statut='publie')
    texte = (request.POST.get('texte') or '').strip()
    parent = None
    parent_id = request.POST.get('parent')
    if parent_id:
        parent = Commentaire.objects.filter(pk=parent_id, contribution=pub, parent__isnull=True).first()

    # Anti-spam : pas plus d'un commentaire toutes les 15 s, ni plus de 15 par heure.
    from datetime import timedelta

    from django.utils import timezone
    maintenant = timezone.now()
    recents = request.user.commentaires.filter(date__gte=maintenant - timedelta(seconds=15))
    par_heure = request.user.commentaires.filter(date__gte=maintenant - timedelta(hours=1)).count()
    if recents.exists():
        messages.error(request, "Vous commentez trop vite. Patientez quelques secondes.")
        return redirect(pub.get_absolute_url() + '#commentaires')
    if par_heure >= 15:
        messages.error(request, "Vous avez atteint la limite de commentaires. Réessayez plus tard.")
        return redirect(pub.get_absolute_url() + '#commentaires')

    if texte:
        commentaire = Commentaire.objects.create(contribution=pub, auteur=request.user,
                                                 texte=texte[:3000], parent=parent)
        # Notifie l'auteur de la publication et, pour une reponse, l'auteur du commentaire parent.
        Notification.creer(pub.auteur, request.user, Notification.COMMENTAIRE, pub, commentaire)
        if parent and parent.auteur_id != pub.auteur_id:
            Notification.creer(parent.auteur, request.user, Notification.REPONSE, pub, commentaire)
    else:
        messages.error(request, 'Votre commentaire est vide.')
    return redirect(pub.get_absolute_url() + '#commentaires')


@login_required
@require_POST
def supprimer_commentaire(request, pk):
    """L'auteur du commentaire (ou le superadmin) le supprime."""
    from django.shortcuts import get_object_or_404
    commentaire = get_object_or_404(Commentaire, pk=pk)
    if commentaire.auteur_id != request.user.id and not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Action non autorisée.')
    url = commentaire.contribution.get_absolute_url()
    commentaire.delete()
    return redirect(url + '#commentaires')


@login_required
@require_POST
def favori(request, pk):
    """Bascule le « lire plus tard ». Répond en JSON (fetch, sans rechargement)."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    pub = get_object_or_404(Contribution, pk=pk, statut='publie')
    existant = Favori.objects.filter(user=request.user, contribution=pub).first()
    if existant:
        existant.delete()
        actif = False
    else:
        Favori.objects.create(user=request.user, contribution=pub)
        actif = True
    return JsonResponse({'favori': actif})


@login_required
def mes_favoris(request):
    """Liste des publications mises de côté par l'utilisateur."""
    favoris = request.user.favoris.select_related('contribution', 'contribution__auteur')
    publications = [f.contribution for f in favoris if f.contribution.statut == 'publie']
    return render(request, 'comptes/mes_favoris.html', {'publications': publications})


def _superadmin(user):
    from django.core.exceptions import PermissionDenied
    if not user.is_superuser:
        raise PermissionDenied


@login_required
def moderation(request):
    """Tableau de bord de modération (superadmin) : file d'attente triée par l'IA."""
    _superadmin(request.user)
    en_attente = (Contribution.objects.filter(statut='attente')
                  .select_related('auteur', 'auteur__profil')
                  .order_by('-moderation_score', '-date'))
    return render(request, 'comptes/moderation.html', {'contributions': en_attente})


@login_required
@require_POST
def moderer(request, pk):
    """Approuve ou rejette une contribution (superadmin), avec notification à l'auteur."""
    _superadmin(request.user)
    from django.shortcuts import get_object_or_404
    contrib = get_object_or_404(Contribution, pk=pk)
    action = request.POST.get('action')
    if action == 'approuver':
        contrib.statut = 'publie'
        contrib.save(update_fields=['statut'])
        messages.success(request, 'Contribution publiée.')
    elif action == 'rejeter':
        contrib.statut = 'refuse'
        contrib.save(update_fields=['statut'])
        messages.warning(request, 'Contribution rejetée.')
    return redirect('moderation')


@login_required
def notifications(request):
    """Liste des notifications de l'utilisateur ; marque tout comme lu à la visite."""
    notifs = request.user.notifications.select_related('acteur', 'acteur__profil', 'contribution')[:50]
    liste = list(notifs)
    request.user.notifications.filter(lu=False).update(lu=True)
    return render(request, 'comptes/notifications.html', {'notifs': liste})


@login_required
@require_POST
def reagir(request, pk):
    """Bascule le « J'aime » de l'utilisateur. Repond en JSON (fetch, sans rechargement)."""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    pub = get_object_or_404(Contribution, pk=pk, statut='publie')
    reaction = Reaction.objects.filter(contribution=pub, auteur=request.user).first()
    if reaction:
        reaction.delete()
        a_aime = False
        # Retire la notification "J'aime" correspondante si non lue.
        Notification.objects.filter(destinataire=pub.auteur, acteur=request.user,
                                    type=Notification.JAIME, contribution=pub, lu=False).delete()
    else:
        Reaction.objects.create(contribution=pub, auteur=request.user)
        a_aime = True
        Notification.creer(pub.auteur, request.user, Notification.JAIME, pub)
    return JsonResponse({'a_aime': a_aime, 'total': pub.reactions.count()})


@login_required
def contribution_modifier(request, pk):
    """L'auteur (et lui seul) modifie sa contribution."""
    from django.shortcuts import get_object_or_404
    contrib = get_object_or_404(Contribution, pk=pk, auteur=request.user)
    profil = getattr(request.user, 'profil', None)
    ptype = profil.type_profil if profil else 'lecteur'
    autorises = Contribution.TYPES_PAR_PROFIL.get(ptype, ['sujet'])
    form = ContributionForm(autorises, request.POST or None, request.FILES or None, instance=contrib)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Votre contribution a été mise à jour.')
        return redirect('compte')
    return render(request, 'comptes/publier.html',
                  {'form': form, 'ptype': ptype, 'profil': profil, 'edition': contrib})


@login_required
def contribution_supprimer(request, pk):
    """L'auteur (et lui seul) supprime sa contribution, apres confirmation."""
    from django.shortcuts import get_object_or_404
    contrib = get_object_or_404(Contribution, pk=pk, auteur=request.user)
    if request.method == 'POST':
        contrib.delete()
        messages.success(request, 'Votre contribution a été supprimée.')
        return redirect('compte')
    return render(request, 'comptes/supprimer.html', {'contrib': contrib})


def telecharger_fichier(request, pk):
    """Telechargement du fichier joint (audio, video, document) d'une publication.

    Accessible a tout visiteur ; sert le fichier en piece jointe.
    """
    from django.http import FileResponse, Http404
    from django.shortcuts import get_object_or_404
    pub = get_object_or_404(Contribution, pk=pk, statut='publie')
    if not pub.fichier:
        raise Http404('Aucun fichier joint.')
    nom = pub.fichier.name.rsplit('/', 1)[-1]
    return FileResponse(pub.fichier.open('rb'), as_attachment=True, filename=nom)
