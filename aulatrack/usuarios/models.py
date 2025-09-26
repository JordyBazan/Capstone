from django.db import models
from django.contrib.auth.models import User




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


# usuarios/models.py

from django.db import models
from django.contrib.auth.models import User

class DocenteCurso(models.Model):
    docente = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'perfil__role': 'docente'})
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('docente', 'curso')









# Create your models here.-------------------------------------------------

class Alumno(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    contacto_emergencia = models.CharField(max_length=15)
    curso = models.ForeignKey("Curso", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - ({self.rut})"
    

class Asignatura(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField()
    profesor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,    
        blank=True    
    )
    


class Curso(models.Model):
    año = models.CharField(max_length=15)
    nombre = models.CharField(max_length=30)
    asignaturas = models.ManyToManyField('Asignatura', blank=True)  # opcional
    profesor_jefe = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,   
        blank=True   
    )
    sala = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.año} {self.nombre} - ({self.sala})"


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