from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, get_object_or_404
from .models import (
    Usuario, Alumno, Asignatura, Curso,
    Asistencia, Anotacion, DocenteCurso, Nota
)

# =========================================================
# FORMULARIO PERSONALIZADO PARA ASISTENCIA
# =========================================================
class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = "__all__"
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),  # ✅ Selector de calendario
        }


# =========================================================
# ASISTENCIA ADMIN (con historial incluido)
# =========================================================
@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    form = AsistenciaForm
    list_display = ("fecha", "alumno", "curso", "estado_coloreado", "ver_historial_link")
    list_filter = ("curso__año", "curso__nombre", "estado", "fecha")
    search_fields = ("alumno__nombres", "alumno__apellidos", "curso__nombre")
    date_hierarchy = "fecha"
    autocomplete_fields = ("alumno", "curso")
    ordering = ("-fecha", "curso__nombre")

    # ----------- Estado coloreado -----------
    def estado_coloreado(self, obj):
        color = {
            "Presente": "#16a34a",   # Verde
            "Ausente": "#dc2626",    # Rojo
            "Justificado": "#facc15" # Amarillo
        }.get(obj.estado, "#6b7280")
        return format_html(f'<b style="color:{color}">{obj.estado}</b>')
    estado_coloreado.short_description = "Estado"

    # ----------- Link directo al historial -----------
    def ver_historial_link(self, obj):
        url = f"/admin/usuarios/asistencia/historial/{obj.alumno.id}/"
        return format_html(f'<a href="{url}" class="button">📅 Ver historial</a>')
    ver_historial_link.short_description = "Historial"

    # ----------- Página de historial -----------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "historial/<int:alumno_id>/",
                self.admin_site.admin_view(self.ver_historial),
                name="asistencia_historial",
            ),
        ]
        return custom_urls + urls

    def ver_historial(self, request, alumno_id):
        alumno = get_object_or_404(Alumno, pk=alumno_id)
        asistencias = (
            Asistencia.objects
            .filter(alumno=alumno)
            .order_by("-fecha")
        )
        presentes = asistencias.filter(estado="Presente").count()
        total = asistencias.count()
        porcentaje = round(presentes / total * 100, 1) if total else 0

        context = dict(
            self.admin_site.each_context(request),
            alumno=alumno,
            asistencias=asistencias,
            total=total,
            presentes=presentes,
            porcentaje=porcentaje,
        )
        return render(request, "admin/asistencia_historial.html", context)


# =========================================================
# USUARIOS
# =========================================================
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("username", "rut", "email", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("username", "rut", "email")
    ordering = ("role", "username")


# =========================================================
# CURSOS
# =========================================================
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("año", "nombre", "sala", "profesor_jefe", "total_alumnos")
    list_filter = ("año",)
    search_fields = ("nombre", "sala")
    ordering = ("año", "nombre")

    def total_alumnos(self, obj):
        return obj.alumno_set.count()
    total_alumnos.short_description = "N° Alumnos"


# =========================================================
# ALUMNOS
# =========================================================
@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombres", "apellidos", "curso", "ver_historial")
    search_fields = ("rut", "nombres", "apellidos")
    list_filter = ("curso__año", "curso__nombre")
    autocomplete_fields = ("curso",)

    def ver_historial(self, obj):
        url = f"/admin/usuarios/asistencia/historial/{obj.id}/"
        return format_html(f'<a href="{url}" class="button"> Ver historial</a>')
    ver_historial.short_description = "Historial de Asistencia"


# =========================================================
# ASIGNATURAS
# =========================================================
@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "curso", "profesor")
    search_fields = ("nombre", "curso__nombre", "profesor__username")
    list_filter = ("curso__año", "profesor")
    autocomplete_fields = ("curso", "profesor")


# =========================================================
# NOTAS
# =========================================================
@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'asignatura', 'curso', 'numero', 'valor_coloreado', 'profesor')
    list_filter = (
        'asignatura__curso__año',
        'asignatura__curso__nombre',
        'asignatura__nombre',
        'profesor',
    )
    search_fields = (
        'alumno__nombres',
        'alumno__apellidos',
        'asignatura__nombre',
        'asignatura__curso__nombre',
    )
    autocomplete_fields = ("alumno", "asignatura", "profesor")
    ordering = ("asignatura__curso__año", "asignatura__nombre", "numero")

    def curso(self, obj):
        return obj.asignatura.curso
    curso.short_description = "Curso"

    def valor_coloreado(self, obj):
        color = "#16a34a" if obj.valor >= 4 else "#dc2626"
        return format_html(f"<b style='color:{color}'>{obj.valor:.1f}</b>")
    valor_coloreado.short_description = "Nota"


# =========================================================
# ANOTACIONES
# =========================================================
@admin.register(Anotacion)
class AnotacionAdmin(admin.ModelAdmin):
    list_display = ("alumno", "profesor", "fecha", "texto_resumen")
    list_filter = ("profesor", "fecha")
    search_fields = ("alumno__nombres", "alumno__apellidos", "texto")
    autocomplete_fields = ("alumno", "profesor")
    date_hierarchy = "fecha"

    def texto_resumen(self, obj):
        return (obj.texto[:60] + "...") if len(obj.texto) > 60 else obj.texto
    texto_resumen.short_description = "Detalle"


# =========================================================
# DOCENTE-CURSO
# =========================================================
@admin.register(DocenteCurso)
class DocenteCursoAdmin(admin.ModelAdmin):
    list_display = ("docente", "curso")
    list_filter = ("curso__año", "curso__nombre", "docente")
    search_fields = ("curso__nombre", "docente__username")
    autocomplete_fields = ("docente", "curso")
