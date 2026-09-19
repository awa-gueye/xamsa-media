# -*- coding: utf-8 -*-
from django import forms

from .models import Bibliotheque


class BibliothequeForm(forms.ModelForm):
    """Ajout d'une production à la bibliothèque, depuis la page (front)."""
    class Meta:
        model = Bibliotheque
        fields = ['type', 'titre', 'description', 'image', 'fichier', 'lien', 'video_url']
        widgets = {
            'titre': forms.TextInput(attrs={'placeholder': 'Titre de la production'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brève description (optionnel).'}),
            'lien': forms.URLInput(attrs={'placeholder': 'https://... (optionnel)'}),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://youtube.com/... (optionnel)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            if not isinstance(f.widget, forms.ClearableFileInput):
                f.widget.attrs.setdefault('class', 'inp')

    def clean_image(self):
        from core.validators import valider_image
        return valider_image(self.cleaned_data.get('image'))

    def clean_fichier(self):
        from core.validators import valider_fichier
        return valider_fichier(self.cleaned_data.get('fichier'))

    def clean(self):
        c = super().clean()
        # Au moins un contenu : fichier, lien ou vidéo (sinon la fiche est vide).
        if not (c.get('fichier') or c.get('lien') or c.get('video_url')):
            raise forms.ValidationError(
                "Ajoutez au moins un fichier, un lien externe ou une vidéo YouTube.")
        return c
