# =========================================================
# forms.py - AulaTrack
# =========================================================
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.forms import CheckboxSelectMultiple
from django.db.models.functions import Lower

# Modelos
from .models import Curso, Asignatura, Usuario, Alumno, DocenteCurso

Usuario = get_user_model()

# =========================================================
# 1) Autenticación (Login)
# =========================================================
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "RUT o Usuario"})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar estilo AulaTrack a todos los campos del Login
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control input-aula'

# =========================================================
# 2) Registro de Usuario
# =========================================================
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
        ]
        # Nota: UserCreationForm ya maneja password1 y password2 internamente,
        # no es necesario declararlos en 'fields' si usas la clase base, 
        # pero si los quieres explícitos para el orden, está bien.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- INYECCIÓN DE ESTILOS CSS ---
        for field_name, field in self.fields.items():
            # Clase base para todos
            css_class = 'form-control input-aula'
            
            # Ajuste especial para Selects (como el Rol)
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select input-aula'
            
            field.widget.attrs.update({
                'class': css_class,
                'placeholder': field.label  # Placeholder automático
            })

    def save(self, commit=True):
        user = super().save(commit=False)
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
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Matemáticas", "class": "form-control input-aula"}),
            "descripcion": forms.Textarea(attrs={"placeholder": "Breve descripción", "rows": 2, "class": "form-control input-aula"}),
            "profesor": forms.Select(attrs={"class": "form-select input-aula"}),
            "curso": forms.Select(attrs={"class": "form-select input-aula"}),
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
            "año": forms.TextInput(attrs={"placeholder": "Ej: 2025", "class": "form-control input-aula"}),
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: 1° Básico A", "class": "form-control input-aula"}),
            "sala": forms.TextInput(attrs={"placeholder": "Ej: Aula 1", "class": "form-control input-aula"}),
            "profesor_jefe": forms.Select(attrs={"data-placeholder": "Seleccione un Docente", "class": "form-select input-aula"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profesor_jefe"].queryset = (
            Usuario.objects.filter(is_active=True, role=Usuario.ROLE_DOCENTE)
            .order_by('nombres', 'apellidos', 'username')
        )
        self.fields["profesor_jefe"].label_from_instance = (
            lambda u: f"{u.get_full_name()} ({u.username})".strip() if u.get_full_name() else f"{u.username}"
        )

    def clean_profesor_jefe(self):
        prof = self.cleaned_data.get("profesor_jefe")
        if prof and getattr(prof, 'role', '') != Usuario.ROLE_DOCENTE:
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
        widget=CheckboxSelectMultiple, # Los checkboxes suelen llevar estilos distintos, no input-aula
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
        widgets = {
             "año": forms.TextInput(attrs={"class": "form-control input-aula"}),
             "nombre": forms.TextInput(attrs={"class": "form-control input-aula"}),
             "sala": forms.TextInput(attrs={"class": "form-control input-aula"}),
        }

# =========================================================
# 4) Asignaciones Docentes
# =========================================================

class AsignarProfesorJefeForm(forms.Form):
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all().order_by('año', 'nombre'),
        label="Curso",
        widget=forms.Select(attrs={"class": "form-select input-aula"})
    )
    docente = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(role='docente').order_by('username'),
        label="Docente (profesor jefe)",
        widget=forms.Select(attrs={"class": "form-select input-aula"})
    )

    def __init__(self, *args, **kwargs):
        initial_curso = kwargs.pop("initial_curso", None)
        super().__init__(*args, **kwargs)
        if initial_curso:
            self.fields["curso"].initial = initial_curso

# =========================================================
# 5) Alumno
# =========================================================

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ['rut', 'nombres', 'apellidos', 'fecha_nacimiento', 'contacto_emergencia', 'curso']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control input-aula'}),
            'rut': forms.TextInput(attrs={'class': 'form-control input-aula'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control input-aula'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control input-aula'}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control input-aula'}),
            'curso': forms.Select(attrs={'class': 'form-select input-aula'}),
        }

class AsignarAsignaturasForm(forms.Form):
    asignaturas = forms.ModelMultipleChoiceField(
        queryset=Asignatura.objects.filter(curso__isnull=True).order_by("nombre"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Asignaturas disponibles"
    )

class AsignarDocenteCursoForm(forms.ModelForm):
    class Meta:
        model = DocenteCurso
        fields = ["docente", "curso"]
        widgets = {
            "docente": forms.Select(attrs={"class": "form-select input-aula"}),
            "curso": forms.Select(attrs={"class": "form-select input-aula"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        docente = cleaned_data.get("docente")
        curso = cleaned_data.get("curso")

        if docente and curso:
            if DocenteCurso.objects.filter(docente=docente, curso=curso).exists():
                raise forms.ValidationError(
                    f"El docente «{docente.username}» ya está asignado al curso «{curso.nombre}»."
                )
        return cleaned_data