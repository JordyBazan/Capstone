from django.contrib import admin
from .models import (
    Usuario, Alumno, Asignatura, Curso,
    Asistencia, Anotacion, DocenteCurso, Nota
)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("username", "rut", "email", "role")
    list_filter = ("role",)
    search_fields = ("username", "rut", "email")

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return True


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombres", "apellidos", "curso")
    search_fields = ("rut", "nombres", "apellidos")
    list_filter = ("curso",)

@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "profesor")
    search_fields = ("nombre",)
    list_filter = ("profesor",)

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("año", "nombre", "sala", "profesor_jefe")
    search_fields = ("año", "nombre", "sala")
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
    search_fields = ("curso__nombre",)

@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'asignatura', 'numero', 'valor', 'profesor')
    list_filter = ('asignatura', 'profesor')
    search_fields = ('alumno__nombres', 'alumno__apellidos', 'asignatura__nombre')
