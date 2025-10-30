# usuarios/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views  
from django.views.generic.base import RedirectView

from .views import (
    home, curso, asistencia, seleccionar_asignatura, libro_notas,
    anotaciones_curso, anotaciones_alumno, reportes,
    crear_curso, crear_asignatura,
    curso_editar, curso_eliminar, asignar_asignaturas_curso,
    curso_quitar_asignatura,cursos_export_pdf,
    asignatura_list, asignatura_editar, asignatura_eliminar,
    asignar_profesor_jefe, asignar_profesor_jefe_inline,
    agregar_alumno, editar_alumno, cursos_lista, MiLoginView, registro
)

app_name = 'usuarios'

urlpatterns = [
    # =============================
    # Páginas principales
    # =============================
    path('', home, name='home'),          
    path('home/', home, name='home_page'),

    # =============================
    # Cursos
    # =============================
    path('curso/<int:curso_id>/', curso, name='curso'),
    path('asistencia/<int:curso_id>/', asistencia, name='asistencia'),
    path('curso/<int:curso_id>/notas/', seleccionar_asignatura, name='notas'),
    path('curso/<int:curso_id>/asignatura/<int:asignatura_id>/notas/', libro_notas, name='libro_notas'),

    # =============================
    # Anotaciones
    # =============================
    path('anotaciones/<int:curso_id>/', anotaciones_curso, name='anotaciones_curso'),
    path('anotaciones/alumno/<int:alumno_id>/', anotaciones_alumno, name='anotaciones_alumno'),

    # =============================
    # Reportes
    # =============================
    path('reportes/', reportes, name='reportes'),
    path('historial/', views.historial_acciones_admin, name='historial_admin'),
    path("historial/eliminar/<int:log_id>/", views.eliminar_log, name="eliminar_log"),
    path("historial/eliminar_todos/", views.eliminar_todos_logs, name="eliminar_todos_logs"),


    # =============================
    # Autenticación
    # =============================
    path('login/', MiLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registro/', registro, name='registro'),

    # =============================
    # Gestión Académica: Cursos
    # =============================
    path('cursos/', cursos_lista, name='cursos_lista'),
    path('cursos/crear/', crear_curso, name='crear_curso'),
    path('cursos/<int:pk>/editar/', curso_editar, name='curso_editar'),
    path('cursos/<int:pk>/eliminar/', curso_eliminar, name='curso_eliminar'),
    path('cursos/<int:curso_id>/asignaturas/', asignar_asignaturas_curso, name='asignar_asignaturas_curso'),
    path('cursos/<int:curso_id>/asignaturas/<int:asignatura_id>/quitar/', curso_quitar_asignatura, name='curso_quitar_asignatura'),
    path('cursos/export/pdf/', cursos_export_pdf, name='cursos_export_pdf'),
    path("mis_cursos/", RedirectView.as_view(pattern_name="usuarios:home_page"), name="mis_cursos"),
    path("reporte_alumno/<int:alumno_id>/pdf/", views.reporte_alumno, name="reporte_alumno"),

    # =============================
    # Gestión Académica: Asignaturas
    # =============================
    path('asignaturas/', asignatura_list, name='asignatura_list'),
    path('asignaturas/crear/', crear_asignatura, name='crear_asignatura'),
    path('asignaturas/<int:pk>/editar/', asignatura_editar, name='asignatura_editar'),
    path('asignaturas/<int:pk>/eliminar/', asignatura_eliminar, name='asignatura_eliminar'),
    path('asignar-profesor-jefe/', asignar_profesor_jefe, name='asignar_profesor_jefe'),
    path('cursos/set-pj/', asignar_profesor_jefe_inline, name='asignar_profesor_jefe_inline'),

    # =============================
    # Gestión Académica: Alumnos
    # =============================
    path('alumnos/nuevo/', agregar_alumno, name='agregar_alumno'),
    path('alumnos/<int:alumno_id>/editar/', editar_alumno, name='editar_alumno'),
    path('alumnos/eliminar/<int:id>/', views.eliminar_alumno, name='eliminar_alumno'),

    # =============================
    # Gestión Académica: Usuarios
    # =============================
    path('gestion_usuario/', views.gestion_usuario, name='gestion_usuario'),
    path('usuario/eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuario/editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
]