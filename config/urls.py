"""Routage principal de Xamsa Media."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as _serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('comptes.urls')),
    path('', include('core.urls')),
    path('actualites/', include('redaction.urls')),
    path('assistant/', include('assistant.urls')),
]

# Fichiers medias (logos, photos, images des contributions) servis en dev ET en
# production. En prod (DEBUG=0), Django ne les sert pas par defaut : on le fait
# ici explicitement (volume de taille modeste, adapte au palier gratuit).
_media = settings.MEDIA_URL.strip('/')
urlpatterns += [
    re_path(r'^%s/(?P<path>.*)$' % _media, _serve, {'document_root': settings.MEDIA_ROOT}),
]
