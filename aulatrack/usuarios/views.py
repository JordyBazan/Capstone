from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib import messages

from usuarios.models import Alumno,Curso,Asignatura
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


# --- HOME UTP ---

def home(request):
    cursos_asignados = None
    cursos_todos = None

    if request.user.is_authenticated:
        if hasattr(request.user, 'perfil') and request.user.perfil.role == 'docente':
            cursos_asignados = DocenteCurso.objects.filter(docente=request.user).select_related('curso')
        elif hasattr(request.user, 'perfil') and request.user.perfil.role == 'utp':
            cursos_todos = Curso.objects.all().select_related('profesor_jefe')

    return render(request, 'home.html', {
        'cursos_asignados': cursos_asignados,
        'cursos_todos': cursos_todos,
    })

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

# --- UTP ---

from .models import Alumno, Perfil, DocenteCurso   
from .forms import RegistroForm, LoginForm, DocenteCursoForm,CursoEditForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CursoForm

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

def es_utp(user):
    return user.is_authenticated and hasattr(user, 'perfil') and user.perfil.role == 'utp'

@user_passes_test(es_utp)
def cursos_lista(request):
    cursos = (
        Curso.objects
        .all()
        .select_related('profesor_jefe')
        .prefetch_related('asignaturas__profesor')
    )

    docentes_por_curso = {}
    for dc in DocenteCurso.objects.select_related('docente', 'curso'):
        docentes_por_curso.setdefault(dc.curso_id, []).append(dc.docente.username)

    # 👇 nuevo
    asignaturas = Asignatura.objects.select_related('profesor').all()

    return render(request, 'cursos_lista.html', {
        'cursos': cursos,
        'docentes_por_curso': docentes_por_curso,
        'asignaturas': asignaturas,  
    })
    


@user_passes_test(es_utp)
def curso_editar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        form = CursoEditForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado correctamente.')
            return redirect('cursos_lista')
    else:
        form = CursoEditForm(instance=curso)
    return render(request, 'curso_editar.html', {'form': form, 'curso': curso})

@user_passes_test(es_utp)
def curso_eliminar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        curso.delete()
        messages.success(request, 'Curso eliminado.')
        return redirect('cursos_lista')
    return render(request, 'curso_eliminar_confirmar.html', {'curso': curso})


