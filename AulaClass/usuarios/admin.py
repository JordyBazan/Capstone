from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.db.models import F
from .models import (
    Usuario, Alumno, Asignatura, Curso,
    Asistencia, Anotacion, DocenteCurso, Nota
)

# =========================================================
# FILTROS PERSONALIZADOS (Mejora de Búsqueda)
# =========================================================

class RangoNotaFilter(admin.SimpleListFilter):
    """Filtro de semáforo para Notas"""
    title = 'Estado de Aprobación'
    parameter_name = 'rango_nota'

    def lookups(self, request, model_admin):
        return (
            ('rojas', 'Insuficientes (< 4.0)'),
            ('azules', 'Suficientes (≥ 4.0)'),
            ('criticas', 'Críticas (< 3.0)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'rojas':
            return queryset.filter(valor__lt=4.0)
        if self.value() == 'azules':
            return queryset.filter(valor__gte=4.0)
        if self.value() == 'criticas':
            return queryset.filter(valor__lt=3.0)
        return queryset

class CursoAnoFilter(admin.SimpleListFilter):
    """Agrupa cursos por Año para evitar listas duplicadas"""
    title = 'Curso y Año'
    parameter_name = 'curso_real'

    def lookups(self, request, model_admin):
        # Ordenamos por año descendente (lo más nuevo primero)
        cursos = Curso.objects.all().order_by('-año', 'nombre')
        return [(c.id, f"{c.año} | {c.nombre}") for c in cursos]

    def queryset(self, request, queryset):
        if self.value():
            # Filtramos dinámicamente según el modelo (Nota o Alumno)
            if hasattr(queryset.model, 'asignatura'):
                return queryset.filter(asignatura__curso__id=self.value())
            elif hasattr(queryset.model, 'curso'):
                return queryset.filter(curso__id=self.value())
        return queryset

# =========================================================
# FORMULARIO PERSONALIZADO
# =========================================================
class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = "__all__"
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
        }

# =========================================================
# ASISTENCIA ADMIN
# =========================================================
@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    form = AsistenciaForm
    # Optimización: Trae datos relacionados en la misma consulta
    list_select_related = ('alumno', 'curso')
    
    list_display = ("fecha", "alumno_full_name", "curso", "estado_badge", "ver_historial_link")
    list_filter = ("curso__año", "curso__nombre", "estado", "fecha")
    search_fields = ("alumno__nombres", "alumno__apellidos", "curso__nombre")
    date_hierarchy = "fecha"
    autocomplete_fields = ("alumno", "curso")
    ordering = ("-fecha", "curso__nombre")

    @admin.display(description='Alumno', ordering='alumno__apellidos')
    def alumno_full_name(self, obj):
        return f"{obj.alumno.apellidos}, {obj.alumno.nombres}"

    # ----------- Badge Visual Moderno -----------
    def estado_badge(self, obj):
        colors = {
            "Presente": ("#dcfce7", "#166534"), # Fondo verde, Texto verde oscuro
            "Ausente":  ("#fee2e2", "#991b1b"), # Fondo rojo, Texto rojo oscuro
            "Justificado": ("#fef9c3", "#854d0e"), # Fondo amarillo
            "Atraso":   ("#e0e7ff", "#3730a3"), # Fondo azul
        }
        bg, text = colors.get(obj.estado, ("#f3f4f6", "#374151"))
        
        return format_html(
            f"<span style='background-color: {bg}; color: {text}; "
            f"padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 12px;'>"
            f"{obj.estado}</span>"
        )
    estado_badge.short_description = "Estado"

    # ----------- Link Historial -----------
    def ver_historial_link(self, obj):
        url = f"/admin/usuarios/asistencia/historial/{obj.alumno.id}/"
        return format_html(
            f'<a href="{url}" style="background:#6366f1; color:white; padding:4px 8px; '
            f'border-radius:4px; text-decoration:none; font-size:11px;"> Historial</a>'
        )
    ver_historial_link.short_description = "Acciones"

    # ----------- Vistas Personalizadas -----------
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
        asistencias = Asistencia.objects.filter(alumno=alumno).select_related('curso').order_by("-fecha")
        
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
    list_display = ("username", "rut", "email", "role_badge", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("username", "rut", "email")
    ordering = ("role", "username")

    def role_badge(self, obj):
        color = "#3b82f6" if obj.role == 'docente' else "#8b5cf6" # Azul o Violeta
        return format_html(f"<b style='color:{color}'>{obj.get_role_display()}</b>")
    role_badge.short_description = "Rol"

# =========================================================
# CURSOS
# =========================================================
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "sala", "profesor_jefe", "total_alumnos")
    list_filter = ("año",)
    search_fields = ("nombre", "sala", "profesor_jefe__username")
    ordering = ("-año", "nombre")
    autocomplete_fields = ("profesor_jefe",)

    @admin.display(description='Curso', ordering='año')
    def nombre_completo(self, obj):
        return f"{obj.nombre} ({obj.año})"

    def total_alumnos(self, obj):
        return obj.alumno_set.count()
    total_alumnos.short_description = "N° Alumnos"

# =========================================================
# ALUMNOS
# =========================================================
@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_select_related = ('curso',) # Optimización DB
    list_display = ("rut", "apellidos", "nombres", "curso_link", "ver_historial_btn")
    search_fields = ("rut", "nombres", "apellidos")
    
    # Usamos el filtro personalizado también aquí
    list_filter = (CursoAnoFilter, "curso__nombre") 
    autocomplete_fields = ("curso",)

    def curso_link(self, obj):
        return f"{obj.curso.nombre} - {obj.curso.año}"
    curso_link.short_description = "Curso Actual"

    def ver_historial_btn(self, obj):
        url = f"/admin/usuarios/asistencia/historial/{obj.id}/"
        return format_html(f'<a href="{url}" class="button" style="padding:3px 8px;">Ver asistencia</a>')
    ver_historial_btn.short_description = "Historial"

# =========================================================
# ASIGNATURAS
# =========================================================
@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_select_related = ('curso', 'profesor')
    list_display = ("nombre", "curso_info", "profesor")
    search_fields = ("nombre", "curso__nombre", "profesor__username")
    list_filter = ("curso__año", "profesor")
    autocomplete_fields = ("curso", "profesor")

    @admin.display(description='Curso', ordering='curso__año')
    def curso_info(self, obj):
        return f"{obj.curso.nombre} ({obj.curso.año})"

# =========================================================
# NOTAS (OPTIMIZADO Y CORREGIDO)
# =========================================================
@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    # Optimización crucial para no matar la base de datos cargando notas
    list_select_related = ('alumno', 'asignatura', 'asignatura__curso', 'profesor')
    
    list_display = (
        'alumno_full_name', 
        'asignatura_nombre', 
        'curso_info', 
        'numero', 
        'valor_badge', 
        'profesor'
    )
    
    list_filter = (
        RangoNotaFilter,   # <--- filtro semáforo
        CursoAnoFilter,    # <--- filtro ordenado por año
        'asignatura__nombre',
        'profesor',
    )
    
    search_fields = (
        'alumno__nombres', 'alumno__apellidos', 'alumno__rut',
        'asignatura__nombre', 'asignatura__curso__nombre'
    )
    
    autocomplete_fields = ("alumno", "asignatura", "profesor")
    ordering = ("-asignatura__curso__año", "asignatura__curso__nombre", "alumno__apellidos")
    list_per_page = 25

    @admin.display(description='Alumno', ordering='alumno__apellidos')
    def alumno_full_name(self, obj):
        return f"{obj.alumno.apellidos}, {obj.alumno.nombres}"

    @admin.display(description='Asignatura', ordering='asignatura__nombre')
    def asignatura_nombre(self, obj):
        return obj.asignatura.nombre

    @admin.display(description='Curso', ordering='asignatura__curso__año')
    def curso_info(self, obj):
        return f"{obj.asignatura.curso.año} | {obj.asignatura.curso.nombre}"

    def valor_badge(self, obj):
        # Estilo Badge igual que Asistencia
        bg = "#dcfce7" if obj.valor >= 4 else "#fee2e2"
        text = "#166534" if obj.valor >= 4 else "#991b1b"
        
        # FORZAR PUNTO EN VEZ DE COMA
        valor_final = f"{obj.valor:.1f}".replace(",", ".")
        
        return format_html(
            f"<span style='background-color: {bg}; color: {text}; "
            f"padding: 4px 12px; border-radius: 99px; font-weight: 800;'>"
            f"{valor_final}</span>"
        )
    valor_badge.short_description = "Nota"
    valor_badge.admin_order_field = 'valor'

# =========================================================
# ANOTACIONES
# =========================================================
@admin.register(Anotacion)
class AnotacionAdmin(admin.ModelAdmin):
    list_select_related = ('alumno', 'profesor')
    list_display = ("fecha", "alumno", "profesor", "texto_resumen")
    list_filter = ("profesor", "fecha")
    search_fields = ("alumno__nombres", "alumno__apellidos", "texto")
    autocomplete_fields = ("alumno", "profesor")
    date_hierarchy = "fecha"

    def texto_resumen(self, obj):
        return (obj.texto[:60] + "...") if len(obj.texto) > 60 else obj.texto
    texto_resumen.short_description = "Observación"

# =========================================================
# DOCENTE-CURSO
# =========================================================
@admin.register(DocenteCurso)
class DocenteCursoAdmin(admin.ModelAdmin):
    list_select_related = ('docente', 'curso')
    list_display = ("docente", "curso_full")
    list_filter = ("curso__año", "docente")
    search_fields = ("curso__nombre", "docente__username")
    autocomplete_fields = ("docente", "curso")

    def curso_full(self, obj):
        return f"{obj.curso.nombre} ({obj.curso.año})"
    curso_full.short_description = "Curso Asignado"