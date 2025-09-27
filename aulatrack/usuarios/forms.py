from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Curso, Asignatura, DocenteCurso, Perfil
from django.forms import CheckboxSelectMultiple




class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Perfil.ROLE_CHOICES, label="Rol")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "role")


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Matemática'}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Breve descripción…', 'rows': 5}),
        }


class DocenteCursoForm(forms.ModelForm):
    class Meta:
        model = DocenteCurso
        fields = ['docente', 'curso']

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['año', 'nombre', 'sala']
        widgets = {
            'año': forms.TextInput(attrs={'placeholder':'Ej:2025 / 1° Básico'}),
            'nombre': forms.TextInput(attrs={'placeholder':'Ej:1° Básico A'}),
            'sala': forms.TextInput(attrs={'placeholder':'Ej:Aula 1'}),
        }

        
class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['nombre', 'descripcion'] 




class CursoEditForm(forms.ModelForm):
    asignaturas = forms.ModelMultipleChoiceField(
        queryset=Asignatura.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple,
        label="Asignaturas"
    )

    class Meta:
        model = Curso
        fields = ['año', 'nombre', 'sala', 'asignaturas']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        

        def label_asignatura(a: Asignatura):
            return f"Asignatura: {a.nombre}"
        self.fields['asignaturas'].label_from_instance = label_asignatura
