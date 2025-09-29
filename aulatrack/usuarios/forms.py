# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.forms import CheckboxSelectMultiple

from .models import Curso, Asignatura, DocenteCurso, Perfil


# ---------- LOGIN ----------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "placeholder": "Tu nombre de usuario"
        }),
        error_messages={"required": "El campo Usuario es obligatorio."}
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        error_messages={"required": "La contraseña es obligatoria."}
    )

    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos. Intenta nuevamente.",
        "inactive": "Esta cuenta está inactiva.",
    }


# ---------- REGISTRO ----------
class RegistroForm(UserCreationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={"placeholder": "Ej: jlopez"}),
        error_messages={"required": "El campo Usuario es obligatorio."}
    )
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "ejemplo@correo.com"}),
        error_messages={
            "required": "El correo electrónico es obligatorio.",
            "invalid": "Ingresa un correo electrónico válido."
        }
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Mínimo 8 caracteres"}),
        error_messages={"required": "Debes ingresar una contraseña."}
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Repite tu contraseña"}),
        error_messages={"required": "Debes confirmar tu contraseña."}
    )
    role = forms.ChoiceField(
        choices=Perfil.ROLE_CHOICES,
        label="Rol",
        error_messages={"required": "Debes seleccionar un rol."}
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "role")
        help_texts = {f: "" for f in ("username", "password1", "password2")}
        error_messages = {
            "username": {
                "unique": "Este nombre de usuario ya está en uso.",
                "required": "El campo Usuario es obligatorio.",
            },
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned


# ---------- GESTIÓN ACADÉMICA ----------
class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ["nombre", "descripcion"]
        labels = {"nombre": "Nombre", "descripcion": "Descripción"}
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej. Matemática"}),
            "descripcion": forms.Textarea(attrs={"placeholder": "Breve descripción…", "rows": 4}),
        }


class DocenteCursoForm(forms.ModelForm):
    class Meta:
        model = DocenteCurso
        fields = ["docente", "curso"]
        labels = {"docente": "Docente", "curso": "Curso"}




from django.db.models.functions import Lower


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["año", "nombre", "sala", "profesor_jefe"]
        labels = {
            "año": "Año",
            "nombre": "Nombre",
            "sala": "Sala",
            "profesor_jefe": "Profesor Jefe (Docente)",
        }
        widgets = {
            "año": forms.TextInput(attrs={"placeholder": "Ej: 2025"}),
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: 1° Básico A"}),
            "sala": forms.TextInput(attrs={"placeholder": "Ej: Aula 1"}),
            "profesor_jefe": forms.Select(attrs={"data-placeholder": "Seleccione un Docente"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["profesor_jefe"].queryset = (
            User.objects.filter(is_active=True, perfil__role='docente')
            .order_by('first_name', 'last_name', 'username')
        )

        self.fields["profesor_jefe"].label_from_instance = (
            lambda u: f"{u.get_full_name()} ({u.username})".strip()
            if u.get_full_name() else f"{u.username}"
        )

    def clean_profesor_jefe(self):
        prof = self.cleaned_data.get("profesor_jefe")
        if prof:
            if not hasattr(prof, "perfil") or prof.perfil.role != "docente":
                raise forms.ValidationError("El usuario seleccionado no tiene rol de Docente.")
        return prof

    def clean(self):
        cleaned = super().clean()
        anio = (cleaned.get("año") or "").strip()
        nombre = (cleaned.get("nombre") or "").strip()
        sala = (cleaned.get("sala") or "").strip()

        if anio and nombre and sala:
            qs = Curso.objects.all()
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            dup = qs.annotate(
                anio_l=Lower("año"),
                nombre_l=Lower("nombre"),
                sala_l=Lower("sala"),
            ).filter(
                anio_l=anio.lower(),
                nombre_l=nombre.lower(),
                sala_l=sala.lower(),
            ).exists()

            if dup:
                self.add_error(None, "Ya existe un curso con el mismo Año, Nombre y Sala.")
        return cleaned


class CursoEditForm(forms.ModelForm):
    asignaturas = forms.ModelMultipleChoiceField(
        queryset=Asignatura.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple,
        label="Asignaturas"
    )

    class Meta:
        model = Curso
        fields = ["año", "nombre", "sala", "asignaturas"]
        labels = {"año": "Año", "nombre": "Nombre", "sala": "Sala"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def label_asignatura(a: Asignatura):
            return f"Asignatura: {a.nombre}"
        self.fields["asignaturas"].label_from_instance = label_asignatura
