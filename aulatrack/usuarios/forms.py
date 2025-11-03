# =========================================================
# Importaciones
# =========================================================
from pyexpat.errors import messages
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.forms import CheckboxSelectMultiple
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, redirect

from .models import Curso, Asignatura, Usuario, Alumno

# =========================================================
# 1) Autenticación
# =========================================================
from django.contrib.auth import get_user_model

Usuario = get_user_model()  

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Tu nombre de usuario"})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"})
    )


# =========================================================
# 2) Registro
# =========================================================
from django.contrib.auth.hashers import make_password
from .models import Usuario


class RegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = [
            'username',
            'nombres',
            'apellidos',
            'rut',
            'email',
            'role',
            'password1',
            'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Esto asegura que los campos extra se guarden bien
        user.nombres = self.cleaned_data.get('nombres')
        user.apellidos = self.cleaned_data.get('apellidos')
        user.rut = self.cleaned_data.get('rut')
        user.email = self.cleaned_data.get('email')
        user.role = self.cleaned_data.get('role')
        if commit:
            user.save()
        return user
# =========================================================
# 3) Gestión Académica
# =========================================================
# 3.1) Asignatura
class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ["nombre", "descripcion", "profesor", "curso"]
        labels = {
            "nombre": "Nombre de la asignatura",
            "descripcion": "Descripción",
            "profesor": "Profesor",
            "curso": "Curso",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Matemáticas"}),
            "descripcion": forms.Textarea(attrs={"placeholder": "Breve descripción", "rows": 2}),
            "profesor": forms.Select(),
            "curso": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profesor"].queryset = Usuario.objects.filter(
            role=Usuario.ROLE_DOCENTE, is_active=True
        ).order_by("nombres", "apellidos")
        self.fields["curso"].queryset = Curso.objects.all().order_by("año", "nombre")

# 3.2) Curso (crear)
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
        # Usar el modelo Usuario y filtrar por rol DOCENTE
        self.fields["profesor_jefe"].queryset = (
            Usuario.objects.filter(is_active=True, role=Usuario.ROLE_DOCENTE)
            .order_by('nombres', 'apellidos', 'username')
        )
        # Mostrar nombre completo y username
        self.fields["profesor_jefe"].label_from_instance = (
            lambda u: f"{u.get_full_name()} ({u.username})".strip() if u.get_full_name() else f"{u.username}"
        )

    def clean_profesor_jefe(self):
        prof = self.cleaned_data.get("profesor_jefe")
        if prof and prof.role != Usuario.ROLE_DOCENTE:
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

# 3.3) Curso: asignar Asignaturas (checkboxes)
class CursoAsignaturasForm(forms.ModelForm):
    asignaturas = forms.ModelMultipleChoiceField(
        queryset=Asignatura.objects.select_related("profesor").order_by("nombre"),
        required=False,
        widget=CheckboxSelectMultiple,
        label="Asignaturas del curso",
    )

    class Meta:
        model = Curso
        fields = ["asignaturas"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def etiqueta(a: Asignatura):
            if a.profesor:
                prof = (a.profesor.get_full_name() or a.profesor.username).strip()
                return f"{a.nombre} — {prof}"
            return a.nombre

        self.fields["asignaturas"].label_from_instance = etiqueta


class CursoEditForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['año', 'nombre', 'sala'] 

# =========================================================
# 4) Docente ↔ Curso (asignación 1 a 1 por fila)
# =========================================================



class AsignarProfesorJefeForm(forms.Form):
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all().order_by('año', 'nombre'),
        label="Curso",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    docente = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(role='docente').order_by('username'),
        label="Docente (profesor jefe)",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        initial_curso = kwargs.pop("initial_curso", None)
        super().__init__(*args, **kwargs)
        if initial_curso:
            self.fields["curso"].initial = initial_curso

from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
get_object_or_404, redirect, messages


@require_POST
def asignar_profesor_jefe(request):
    if getattr(request.user.usuario, 'role', None) != 'utp':
        raise PermissionDenied("Solo UTP puede asignar profesor jefe.")

    curso_id = request.POST.get('curso_id')
    pj_id = request.POST.get('profesor_jefe')  

    curso = get_object_or_404(Curso, pk=curso_id)

    if pj_id:
        pj = get_object_or_404(User, pk=pj_id, usuario__role='docente')
        curso.profesor_jefe = pj
        msg = f"Profesor Jefe asignado: {pj.get_full_name() or pj.username}"
    else:
        curso.profesor_jefe = None
        msg = "Profesor Jefe eliminado."

    curso.save(update_fields=['profesor_jefe'])
    messages.success(request, msg)
    return redirect('curso_editar', pk=curso.pk)


# =========================================================
# 5) Alumno
# =========================================================

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ['rut', 'nombres', 'apellidos', 'fecha_nacimiento', 'contacto_emergencia', 'curso']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

class AsignarAsignaturasForm(forms.Form):
    asignaturas = forms.ModelMultipleChoiceField(
        queryset=Asignatura.objects.filter(curso__isnull=True).order_by("nombre"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Asignaturas disponibles"
    )

    