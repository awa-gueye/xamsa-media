from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('hors-ligne/', views.hors_ligne, name='hors_ligne'),
    path('recherche/', views.recherche, name='recherche'),
    path('api/latest/', views.latest_json, name='latest_json'),
    path('rubriques/', views.rubriques, name='rubriques'),
    path('rubriques/specialite/<slug:slug>/', views.rubrique_detail, name='rubrique_detail'),
    path('rubriques/medias-senegal/', views.medias_senegal, name='medias_senegal'),
    path('rubriques/medias-senegal/<slug:type_slug>/', views.medias_senegal, name='medias_senegal_type'),
    path('dossiers/', views.dossiers, name='dossiers'),
    path('dossiers/audio-video/', views.audio_video, name='audio_video'),
    path('academie/', views.academie, name='academie'),
    path('academie/<slug:type_slug>/', views.academie, name='academie_type'),
    path('communaute/', views.communaute, name='communaute'),
    path('communaute/<slug:type_slug>/', views.communaute, name='communaute_type'),
]
