# =========================================================
# forms.py - AulaClass
# =========================================================
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.forms import CheckboxSelectMultiple
from django.db.models import Q
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
        # Nota: AbstractUser suele tener username de 150 caracteres
        widget=forms.TextInput(attrs={
            "autofocus": True, 
            "placeholder": "Usuario",
            "maxlength": "150" 
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "placeholder": "••••••••",
            "maxlength": "128" # Estándar de Django hashing
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar estilo AulaClass a todos los campos del Login
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
        # Definimos widgets aquí para asegurar los maxlength según el modelo
        widgets = {
            'username': forms.TextInput(attrs={'maxlength': '150'}),
            'nombres': forms.TextInput(attrs={'maxlength': '100'}),
            'apellidos': forms.TextInput(attrs={'maxlength': '100'}),
            'rut': forms.TextInput(attrs={'maxlength': '12'}),
            # EmailField ya valida formato, pero el maxlength ayuda visualmente
            'email': forms.EmailInput(attrs={'maxlength': '254'}), 
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- INYECCIÓN DE ESTILOS CSS ---
        for field_name, field in self.fields.items():
            # Clase base para todos
            css_class = 'form-control input-aula'
            
            # Ajuste especial para Selects (como el Rol)
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select input-aula'
            
            # Actualizamos atributos sin borrar los que definimos en 'widgets'
            field.widget.attrs.update({
                'class': css_class,
                'placeholder': field.label 
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
            "nombre": forms.TextInput(attrs={
                "placeholder": "Ej: Matemáticas", 
                "class": "form-control input-aula",
                "maxlength": "100" # Limite modelo
            }),
            "descripcion": forms.Textarea(attrs={
                "placeholder": "Breve descripción", 
                "rows": 2, 
                "class": "form-control input-aula"
                # TextField no tiene límite estricto en DB, pero podemos poner uno lógico si queremos
            }),
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
            "año": forms.TextInput(attrs={
                "placeholder": "Ej: 2025", 
                "class": "form-control input-aula",
                "maxlength": "15" # Limite modelo
            }),
            "nombre": forms.TextInput(attrs={
                "placeholder": "Ej: 1° Básico A", 
                "class": "form-control input-aula",
                "maxlength": "50" # Limite modelo
            }),
            "sala": forms.TextInput(attrs={
                "placeholder": "Ej: Aula 1", 
                "class": "form-control input-aula",
                "maxlength": "50" # Limite modelo
            }),
            "profesor_jefe": forms.Select(attrs={
                "data-placeholder": "Seleccione un Docente", 
                "class": "form-select input-aula"
            }),
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
        widgets = {
             "año": forms.TextInput(attrs={"class": "form-control input-aula", "maxlength": "15"}),
             "nombre": forms.TextInput(attrs={"class": "form-control input-aula", "maxlength": "50"}),
             "sala": forms.TextInput(attrs={"class": "form-control input-aula", "maxlength": "50"}),
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
            'rut': forms.TextInput(attrs={'class': 'form-control input-aula', 'maxlength': '12'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control input-aula', 'maxlength': '100'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control input-aula', 'maxlength': '100'}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control input-aula', 'maxlength': '50'}),
            'curso': forms.Select(attrs={'class': 'form-select input-aula'}),
        }

class AsignarAsignaturasForm(forms.Form):
    # Inicialmente queryset vacío, lo llenamos en el __init__
    asignaturas = forms.ModelMultipleChoiceField(
        queryset=Asignatura.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Asignaturas Disponibles"
    )

    def __init__(self, *args, **kwargs):
        # Extraemos el argumento 'curso' que pasaremos desde la vista
        curso = kwargs.pop('curso', None) 
        super().__init__(*args, **kwargs)

        if curso:
            self.fields['asignaturas'].queryset = Asignatura.objects.filter(
                Q(curso=curso) | Q(curso__isnull=True)
            )

class AsignarDocenteCursoForm(forms.ModelForm):
    class Meta:
        model = DocenteCurso
        fields = ['docente', 'curso']
        widgets = {
            'docente': forms.Select(attrs={'class': 'control-input'}),
            'curso': forms.Select(attrs={'class': 'control-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Filtrar solo usuarios que sean DOCENTES
        self.fields['docente'].queryset = Usuario.objects.filter(role='docente').order_by('apellidos', 'nombres')
        
        # 2. Mejorar cómo se ven los nombres en el select (Nombre Apellido en vez de username)
        self.fields['docente'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.username})"
        
        # 3. Ordenar cursos
        self.fields['curso'].queryset = Curso.objects.all().order_by('año', 'nombre')
        
        # 4. Textos de ayuda visual (Placeholder)
        self.fields['docente'].empty_label = "Seleccione un docente..."
        self.fields['curso'].empty_label = "Seleccione un curso..."