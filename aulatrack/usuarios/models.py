# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.db.models.functions import Lower

# Validadores
rut_validator = RegexValidator(
    regex=r'^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$',
    message="El RUT debe tener un formato válido, por ejemplo: 12.345.678-9 o 12345678-9"
)

telefono_validator = RegexValidator(
    regex=r'^\+?56\d{9}$',
    message="El número debe tener el formato chileno, por ejemplo: +56912345678"
)

# Modelo Usuario
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


# Otros modelos
class Curso(models.Model):
    año = models.CharField(max_length=15)
    nombre = models.CharField(max_length=30)
    sala = models.CharField(max_length=10)
    profesor_jefe = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'role': 'docente'},
        related_name='cursos_como_profesor_jefe'
    )

    def __str__(self):
        return f"{self.año} {self.nombre} - ({self.sala})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('año'), Lower('nombre'), Lower('sala'),
                name='uniq_curso_anio_nombre_sala_ci'
            )
        ]


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


class Asignatura(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(blank=True)
    profesor = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, null=True, blank=True, limit_choices_to={'role': 'docente'}
    )
    curso = models.ForeignKey(
        'Curso', on_delete=models.CASCADE, related_name='asignaturas', null=True, blank=True
    )

    def __str__(self):
        return f"{self.nombre} ({self.curso.año} {self.curso.nombre})" if self.curso else self.nombre


class DocenteCurso(models.Model):
    docente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'docente'}
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('docente', 'curso')


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

    class Meta:
        ordering = ["alumno", "asignatura", "evaluacion"]


class Asistencia(models.Model):
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10)  # Presente, Ausente, Justificado
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.alumno} - {self.fecha} ({self.estado})"


class Anotacion(models.Model):
    texto = models.TextField()
    fecha = models.DateField(auto_now_add=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    profesor = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return f"Anotación de {self.profesor} para {self.alumno} el {self.fecha}"
