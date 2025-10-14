from django.db import models
from django.contrib.auth.models import User
from django.db.models.functions import Lower
from django.core.validators import RegexValidator





# --- NUEVO: Perfil con rol ---
class Perfil(models.Model):
    ROLE_DOCENTE = 'docente'
    ROLE_UTP = 'utp'
    ROLE_INSPECTOR = 'inspector'
    ROLE_CHOICES = [
        (ROLE_DOCENTE, 'Docente'),
        (ROLE_UTP, 'UTP'),
        (ROLE_INSPECTOR, 'Inspector'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class DocenteCurso(models.Model):
    docente = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'perfil__role': 'docente'})
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('docente', 'curso')









# Create your models here.-------------------------------------------------


# VALIRDAR FORMATO RUT Y TELEFONO.-----------------

rut_validator = RegexValidator(
    regex=r'^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$',
    message="El RUT debe tener un formato válido, por ejemplo: 12.345.678-9 o 12345678-9"
)

telefono_validator = RegexValidator(
    regex=r'^\+?56\d{9}$',
    message="El número debe tener el formato chileno, por ejemplo: +56912345678"
)



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
    curso = models.ForeignKey("Curso", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - ({self.rut})"

    class Meta:
        ordering = ['apellidos', 'nombres']



class Asignatura(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField()
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.nombre
    


class Curso(models.Model):
    año = models.CharField(max_length=15)
    nombre = models.CharField(max_length=30)
    asignaturas = models.ManyToManyField('Asignatura', blank=True)

    profesor_jefe = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'perfil__role': 'docente'}, 
        related_name='cursos_como_profesor_jefe'
    )

    sala = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.año} {self.nombre} - ({self.sala})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('año'), Lower('nombre'), Lower('sala'),
                name='uniq_curso_anio_nombre_sala_ci'
            )
        ]


class Nota(models.Model):
    valor = models.FloatField()
    fecha_registro = models.DateField(auto_now_add=True)
    evaluacion = models.CharField(max_length=50)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE) #REVISAR
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE) #REVISAR
    profesor = models.ForeignKey(User, on_delete=models.CASCADE) #REVISAR
    ultima_actualizacion = models.DateTimeField(auto_now=True) # cada vez que se guarda y REVISAR

    def __str__(self):
        return f"{self.evaluacion} - {self.valor} ({self.alumno})"



class Asistencia(models.Model):
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10)  # Presente, Ausente, justidicado
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE) #REVISAR
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE) #REVISAR

    def __str__(self):
        return f"{self.alumno} - {self.fecha} ({self.estado})"


class Anotacion(models.Model):
    texto = models.TextField()
    fecha = models.DateField(auto_now_add=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE) #REVISAR
    profesor = models.ForeignKey(User, on_delete=models.CASCADE) #REVISAR

    def __str__(self):
        return f"Anotacion de {self.profesor} para {self.alumno} el {self.fecha}"