from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import Perfil


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Perfil.ROLE_CHOICES, label="Rol")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "role")


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)



# usuarios/forms.py

from django import forms
from .models import DocenteCurso, Curso,Asignatura

class DocenteCursoForm(forms.ModelForm):
    class Meta:
        model = DocenteCurso
        fields = ['docente', 'curso']

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['año', 'nombre', 'sala']
        
class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['nombre', 'descripcion'] 
