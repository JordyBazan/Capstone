# urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    MiLoginView, registro, home, curso, asistencia,
    notas, anotaciones, reportes, 
    crear_curso, crear_asignatura
)
from . import views

urlpatterns = [

    # =============================
    # Páginas principales
    # =============================
    path('', home, name='home'),
    path('curso/<int:curso_id>/', views.curso, name='curso'),
    path('asistencia/<int:curso_id>/', views.asistencia, name='asistencia'),
    



    path('curso/<int:curso_id>/notas/', views.seleccionar_asignatura, name='notas'),
    path('curso/<int:curso_id>/asignatura/<int:asignatura_id>/notas/', views.libro_notas, name='libro_notas'),
    path('curso/<int:curso_id>/asignatura/<int:asignatura_id>/notas/', views.libro_notas, name='libro_notas'),




    path('anotaciones/<int:curso_id>/', views.anotaciones_curso, name='anotaciones_curso'),
    path('anotaciones/alumno/<int:alumno_id>/', views.anotaciones_alumno, name='anotaciones_alumno'),



    
    path('reportes/', reportes, name='reportes'),

    # =============================
    # Autenticación
    # =============================
    path('login/', MiLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registro/', registro, name='registro'),

    # =============================
    # Gestión Académica: Cursos
    # =============================
    path('cursos/', views.cursos_lista, name='cursos_lista'),
    path('cursos/crear/', crear_curso, name='crear_curso'),
    path('cursos/<int:pk>/editar/', views.curso_editar, name='curso_editar'),
    path('cursos/<int:pk>/eliminar/', views.curso_eliminar, name='curso_eliminar'),
    path('cursos/<int:curso_id>/asignaturas/', views.asignar_asignaturas_curso, name='asignar_asignaturas_curso'),
    path('alumnos/eliminar/<int:id>/', views.eliminar_alumno, name='eliminar_alumno'),

    path(
        'cursos/<int:curso_id>/asignaturas/<int:asignatura_id>/quitar/',
        views.curso_quitar_asignatura,
        name='curso_quitar_asignatura'
    ),


    # =============================
    # Gestión Académica: Asignaturas
    # =============================
    path('asignaturas/', views.asignatura_list, name='asignatura_list'),
    path('asignaturas/crear/', crear_asignatura, name='asignatura_crear'),
    path('asignaturas/<int:pk>/editar/', views.asignatura_editar, name='asignatura_editar'),
    path('asignaturas/<int:pk>/eliminar/', views.asignatura_eliminar, name='asignatura_eliminar'),

    path('crear-asignatura/', crear_asignatura, name='crear_asignatura'),
    path("asignar-profesor-jefe/", views.asignar_profesor_jefe, name="asignar_profesor_jefe"),         
    path("cursos/set-pj/", views.asignar_profesor_jefe_inline, name="asignar_profesor_jefe_inline"),   

    path('cursos/export/pdf/', views.cursos_export_pdf, name='cursos_export_pdf'),



    # =============================
    # Gestión Académica: Cursos
    # =============================
    
    path('alumnos/nuevo/', views.agregar_alumno, name='agregar_alumno'),

    path('asistencia/<int:curso_id>/', views.asistencia, name='asistencia'),
    path('alumnos/<int:alumno_id>/editar/', views.editar_alumno, name='editar_alumno'),

]
