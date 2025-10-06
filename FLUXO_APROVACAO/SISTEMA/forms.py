from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .models import Usuario, Setor


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Usuário",
        widget=forms.TextInput(attrs={"placeholder": "Digite seu usuário"})
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Digite sua senha"})
    )

class UsuarioCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, label="E-mail")
    setor = forms.ModelChoiceField(queryset=Setor.objects.all(), required=False, label="Setor")
    perfil = forms.ChoiceField(choices=Usuario._meta.get_field('perfil').choices, label="Perfil")
    grupo = forms.ModelChoiceField(queryset=Group.objects.all(), required=True, label="Grupo")

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'setor', 'perfil', 'grupo']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.setor = self.cleaned_data['setor']
        user.perfil = self.cleaned_data['perfil']

        if commit:
            user.save()
            user.groups.add(self.cleaned_data['grupo'])
        return user

Usuario = get_user_model()

class UsuarioEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'setor', 'perfil', 'groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
        self.fields['groups'].label = 'Grupos'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return self.instance.username
        if Usuario.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError('Este nome de usuário já está em uso.')
        return username

