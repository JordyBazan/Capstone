from django.contrib import admin
from .models import (
    Perfil, Alumno, Asignatura, Curso,
    Asistencia, Anotacion, DocenteCurso
)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombres", "apellidos", "curso")
    search_fields = ("rut", "nombres", "apellidos")
    list_filter = ("curso",)

@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "profesor")
    search_fields = ("nombre", "profesor__username")
    list_filter = ("profesor",)

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("año", "nombre", "sala", "profesor_jefe")
    search_fields = ("año", "nombre", "sala", "profesor_jefe__username")
    list_filter = ("año",)


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("alumno", "curso", "fecha", "estado")
    list_filter = ("curso", "estado", "fecha")
    search_fields = ("alumno__nombres", "alumno__apellidos")

@admin.register(Anotacion)
class AnotacionAdmin(admin.ModelAdmin):
    list_display = ("alumno", "profesor", "fecha")
    list_filter = ("profesor", "fecha")
    search_fields = ("alumno__nombres", "alumno__apellidos", "texto")


@admin.register(DocenteCurso)
class DocenteCursoAdmin(admin.ModelAdmin):
    list_display = ("docente", "curso")
    list_filter = ("docente", "curso")
    search_fields = ("docente__username", "curso__nombre")