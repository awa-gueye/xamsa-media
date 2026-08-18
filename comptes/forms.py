# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Profil


class InscriptionForm(forms.Form):
    type_profil = forms.ChoiceField(choices=Profil.TYPES)
    prenom = forms.CharField(max_length=60)
    nom = forms.CharField(max_length=60)
    email = forms.EmailField()
    telephone = forms.CharField(max_length=30, required=False)
    localisation = forms.CharField(max_length=120, required=False)
    organisation = forms.CharField(max_length=160, required=False)
    photo = forms.ImageField(required=False)
    mot_de_passe = forms.CharField(widget=forms.PasswordInput)
    confirmation = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise forms.ValidationError('Un compte existe déjà avec cet email.')
        return email

    def clean(self):
        c = super().clean()
        mp, cf = c.get('mot_de_passe'), c.get('confirmation')
        if mp and cf and mp != cf:
            self.add_error('confirmation', 'Les mots de passe ne correspondent pas.')
        if mp:
            try:
                validate_password(mp)
            except forms.ValidationError as e:
                self.add_error('mot_de_passe', e)
        return c

    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(
            username=d['email'], email=d['email'],
            first_name=d['prenom'], last_name=d['nom'], password=d['mot_de_passe'])
        Profil.objects.create(
            user=user, type_profil=d['type_profil'], telephone=d.get('telephone', ''),
            localisation=d.get('localisation', ''), organisation=d.get('organisation', ''),
            photo=d.get('photo') or None)
        return user


class ConnexionForm(forms.Form):
    email = forms.EmailField()
    mot_de_passe = forms.CharField(widget=forms.PasswordInput)


from .models import Contribution


class ProfilForm(forms.ModelForm):
    """Modification par l'utilisateur de ses informations et de sa photo."""
    prenom = forms.CharField(max_length=60, required=False, label='Prénom')
    nom = forms.CharField(max_length=60, required=False, label='Nom')

    class Meta:
        model = Profil
        fields = ['type_profil', 'telephone', 'localisation', 'organisation', 'bio', 'photo']
        widgets = {
            'telephone': forms.TextInput(attrs={'placeholder': '+221 77 000 00 00'}),
            'localisation': forms.TextInput(attrs={'placeholder': 'Dakar, Sénégal'}),
            'organisation': forms.TextInput(attrs={'placeholder': 'Rédaction, association, université...'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Quelques mots sur vous (visibles sur votre profil public).'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['prenom'].initial = self.instance.user.first_name
            self.fields['nom'].initial = self.instance.user.last_name
        for f in self.fields.values():
            if not isinstance(f.widget, forms.ClearableFileInput):
                f.widget.attrs.setdefault('class', 'inp')

    def save(self, commit=True):
        profil = super().save(commit=False)
        user = profil.user
        user.first_name = self.cleaned_data.get('prenom', '')
        user.last_name = self.cleaned_data.get('nom', '')
        if commit:
            user.save()
            profil.save()
        return profil


class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['type', 'titre', 'categorie', 'resume', 'corps', 'image', 'fichier']
        widgets = {
            'titre': forms.TextInput(attrs={'placeholder': 'Un titre clair et accrocheur'}),
            'categorie': forms.TextInput(attrs={'placeholder': 'Ex. Politique, Medias, Societe'}),
            'resume': forms.Textarea(attrs={'rows': 2, 'placeholder': "Une ou deux phrases qui resument l'essentiel."}),
            'corps': forms.Textarea(attrs={'rows': 12}),
        }

    def __init__(self, types_autorises=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if types_autorises:
            self.fields['type'].choices = [(v, l) for v, l in Contribution.TYPES if v in types_autorises]
        for f in self.fields.values():
            if not isinstance(f.widget, forms.ClearableFileInput):
                f.widget.attrs.setdefault('class', 'inp')
        # L'editeur enrichi ecrit dans ce champ ; on l'identifie pour le JS.
        self.fields['corps'].widget.attrs['class'] = 'inp rich-source'

    def clean_corps(self):
        """Assainit le HTML de l'editeur enrichi (anti-XSS) avant enregistrement."""
        from .sanitize import nettoyer_html
        return nettoyer_html(self.cleaned_data.get('corps', ''))
