from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib import messages

from usuarios.models import Alumno
from .forms import RegistroForm, LoginForm, CursoForm, AsignaturaForm




@login_required
def home(request):
    cursos_asignados = DocenteCurso.objects.filter(docente=request.user).select_related('curso')
    return render(request, 'home.html', {'cursos_asignados': cursos_asignados})

def curso(request):
    return render(request, 'curso.html')

def asistencia(request):
    alumnos = Alumno.objects.all()
    return render(request, 'asistencia.html', {'alumnos': alumnos})

def notas(request):
    return render(request, 'notas.html')

def anotaciones(request):
    return render(request, 'anotaciones.html')

def reportes(request):
    return render(request, 'reportes.html')


# --- LOGIN ---
class MiLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

from .models import Perfil   


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            Perfil.objects.create(user=user, role=form.cleaned_data['role'])

            messages.success(request, "¡Cuenta creada con éxito! Ahora puedes ingresar.")
            auth_login(request, user)  
            return redirect('home')
        else:
            messages.error(request, "Revisa los campos e intenta de nuevo.")
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})


# usuarios/views.py
from .models import Alumno, Perfil, DocenteCurso   # importa tu nuevo modelo
from .forms import RegistroForm, LoginForm, DocenteCursoForm
def es_utp(user):
    return user.is_authenticated and hasattr(user, 'perfil') and user.perfil.role == 'utp'


@user_passes_test(es_utp)
def asignar_docente_curso(request):
    if request.method == 'POST':
        form = DocenteCursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Docente asignado correctamente al curso.")
            return redirect('home')
    else:
        form = DocenteCursoForm()
    return render(request, 'asignar_docente_curso.html', {'form': form})

def es_utp(user):
    return user.is_authenticated and hasattr(user, 'perfil') and user.perfil.role == 'utp'

@user_passes_test(es_utp)
def crear_curso(request):
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso creado con éxito.")
            return redirect('home')
    else:
        form = CursoForm()
    return render(request, 'crear_curso.html', {'form': form})


from .forms import CursoForm

def es_utp(user):
    return user.is_authenticated and hasattr(user, 'perfil') and user.perfil.role == 'utp'

@user_passes_test(es_utp)
def crear_curso(request):
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso creado con éxito.")
            return redirect('home')
    else:
        form = CursoForm()
    return render(request, 'crear_curso.html', {'form': form})


@user_passes_test(es_utp)
def crear_asignatura(request):
    if request.method == 'POST':
        form = AsignaturaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Asignatura creada con éxito.")
            return redirect('home')
    else:
        form = AsignaturaForm()
    return render(request, 'crear_asignatura.html', {'form': form})