from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    MiLoginView, registro, home, curso, asistencia,
    notas, anotaciones, reportes, asignar_docente_curso, crear_curso, crear_asignatura
)

urlpatterns = [
    path('', home, name='home'),
    path('curso/', curso, name='curso'),
    path('asistencia/', asistencia, name='asistencia'),
    path('notas/', notas, name='notas'),
    path('anotaciones/', anotaciones, name='anotaciones'),
    path('reportes/', reportes, name='reportes'),

    path('login/', MiLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registro/', registro, name='registro'),

    path('asignar-docente-curso/', asignar_docente_curso, name='asignar_docente_curso'),
    path('crear-curso/', crear_curso, name='crear_curso'),
    path('crear-asignatura/', crear_asignatura, name='crear_asignatura'),



]
