# =========================================================
# Importaciones
# =========================================================
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.db.models.functions import Lower
from django.utils import timezone
from django.core.exceptions import ValidationError




# =========================================================
# Validadores
# =========================================================

# Alumno
rut_validator = RegexValidator(
    regex=r'^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$',
    message="El RUT debe tener un formato válido, por ejemplo: 12.345.678-9 o 12345678-9"
)

telefono_validator = RegexValidator(
    regex=r'^\+?56\d{9}$',
    message="El número debe tener el formato chileno, por ejemplo: +56912345678"
)



# Curso
año_validator = RegexValidator(
    regex=r'^\d+$',
    message="El campo 'Año' solo puede contener números."
)

sala_validator = RegexValidator(
    regex=r'^[A-Za-z0-9\s-]+$',
    message="El campo 'Sala' solo puede contener letras, números, guiones o espacios."
)






# =========================================================
# Modelos
# =========================================================



# =========================================================
# Modelo Usuario
# =========================================================

class Usuario(AbstractUser):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True, validators=[rut_validator])
    
    ROLE_DOCENTE = 'docente'
    ROLE_UTP = 'utp'
    ROLE_INSPECTOR = 'inspector'
    ROLE_CHOICES = [
        (ROLE_DOCENTE, 'Docente'),
        (ROLE_UTP, 'UTP'),
        (ROLE_INSPECTOR, 'Inspector'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} - {self.nombres} {self.apellidos}"



# =========================================================
# Modelo Curso
# =========================================================
class Curso(models.Model):
    año = models.CharField(max_length=15, validators=[año_validator])
    nombre = models.CharField(max_length=30)
    sala = models.CharField(max_length=10, validators=[sala_validator])
    profesor_jefe = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'docente'},
        related_name='cursos_como_profesor_jefe'
    )

    def __str__(self):
        return f"{self.año} {self.nombre} - ({self.sala})"

    def clean(self):
        # Evita campos vacios
        if not self.año.strip() or not self.nombre.strip() or not self.sala.strip():
            raise ValidationError("Ningún campo puede quedar vacío.")

        # Valida que haya profesor_jefe asignado
        if not self.profesor_jefe:
            raise ValidationError("Debe asignarse un profesor jefe al curso.")

        # Evita duplicados
        if Curso.objects.filter(
            año__iexact=self.año,
            nombre__iexact=self.nombre,
            sala__iexact=self.sala
        ).exclude(id=self.id).exists():
            raise ValidationError("Ya existe un curso con el mismo año, nombre y sala.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Ejecuta todas las validaciones antes de guardar
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('año'), Lower('nombre'), Lower('sala'),
                name='uniq_curso_anio_nombre_sala_ci'
            )
        ]
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"



# =========================================================
# Modelo Alumno
# =========================================================
class Alumno(models.Model):
    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[rut_validator],
        help_text="Formato: 12.345.678-9 o 12345678-9"
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    contacto_emergencia = models.CharField(
        max_length=15,
        validators=[telefono_validator],
        help_text="Formato: +569XXXXXXXX"
    )
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - ({self.rut})"

    class Meta:
        ordering = ['apellidos', 'nombres']



# =========================================================
# Modelo Asignatura
# =========================================================

class Asignatura(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(blank=True)  # puede quedar vacio
    profesor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'docente'}   # obligatorio
    )
    curso = models.ForeignKey(
        'Curso',
        on_delete=models.CASCADE,
        related_name='asignaturas'             # obligatorio
    )

    def __str__(self):
        return f"{self.nombre} ({self.curso.año} {self.curso.nombre})" if self.curso else self.nombre

    # Validaciones de negocio
    def clean(self):
        # nombre no vacío (sin espacios)
        if not self.nombre or not self.nombre.strip():
            raise ValidationError("El campo 'Nombre' no puede quedar vacío.")

        # profesor y curso obligatorios (defensa adicional)
        if not self.profesor:
            raise ValidationError("Debe asignarse un profesor (docente).")
        if not self.curso:
            raise ValidationError("Debe asignarse un curso.")

        # evitar duplicados de nombre dentro del mismo curso (case-insensitive)
        ya_existe = Asignatura.objects.filter(
            nombre__iexact=self.nombre.strip(),
            curso=self.curso
        ).exclude(id=self.id).exists()
        if ya_existe:
            raise ValidationError("Ya existe una asignatura con ese nombre en este curso.")

    def save(self, *args, **kwargs):
        self.full_clean()  # corre validators + clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Asignatura"
        verbose_name_plural = "Asignaturas"
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'curso'],
                name='unique_asignatura_por_curso'
            )
        ]




# =========================================================
# Modelo ??
# =========================================================
class DocenteCurso(models.Model):
    docente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'docente'}
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('docente', 'curso')



# =========================================================
# Modelo Nota
# =========================================================
class Nota(models.Model):
    valor = models.FloatField()
    fecha_registro = models.DateField(auto_now_add=True)
    evaluacion = models.CharField(max_length=50)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    profesor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    numero = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.evaluacion} - {self.valor} ({self.alumno})"

    def detalle_registro(self):
        """Texto útil para mostrar quién y cuándo registró."""
        prof = self.profesor.get_full_name() or self.profesor.username
        fecha = self.ultima_actualizacion.strftime("%d/%m/%Y %H:%M")
        return f"{prof} · {fecha}"

    def fue_editada_recientemente(self):
        """Indica si la nota fue modificada hace menos de 24 horas."""
        return (timezone.now() - self.ultima_actualizacion).days < 1

    class Meta:
        ordering = ["alumno", "asignatura", "evaluacion"]
        unique_together = ("alumno", "asignatura", "numero")



# =========================================================
# Modelo Asistencia
# =========================================================
class Asistencia(models.Model):
    ESTADOS = [
        ("Presente", "Presente"),
        ("Ausente", "Ausente"),
        ("Justificado", "Justificado"),
    ]

    fecha = models.DateField(
        verbose_name="Fecha",
        help_text="Selecciona la fecha de asistencia",
        null=False,
        blank=False
    )
    estado = models.CharField(max_length=15, choices=ESTADOS)
    alumno = models.ForeignKey("Alumno", on_delete=models.CASCADE)
    curso = models.ForeignKey("Curso", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.alumno} - {self.fecha} ({self.estado})"



# =========================================================
# Modelo Anotacion
# =========================================================
class Anotacion(models.Model):
    texto = models.TextField()
    fecha = models.DateField(auto_now_add=True)
    alumno = models.ForeignKey('Alumno', on_delete=models.CASCADE)
    profesor = models.ForeignKey('Usuario', on_delete=models.CASCADE)

    def __str__(self):
        return f"Anotación de {self.profesor} para {self.alumno} el {self.fecha}"