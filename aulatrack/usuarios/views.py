# views.py

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404

# Modelos: evita duplicados y conflictos de nombres
from usuarios.models import Alumno, Curso, Asignatura, Nota
from .models import Perfil, DocenteCurso

# Formularios
from .forms import (
    RegistroForm, LoginForm, DocenteCursoForm,
    CursoEditForm, CursoForm, AsignaturaForm
)

# -------------------------
# Utilidades / Permisos
# -------------------------
def es_utp(user):
    """Permite acceso solo a usuarios con rol UTP."""
    return user.is_authenticated and hasattr(user, 'perfil') and user.perfil.role == 'utp'


# -------------------------
# Páginas principales
# -------------------------
@login_required
def home(request):
    """Dashboard según rol: Docente ve sus cursos; UTP ve todos."""
    cursos_asignados = None
    cursos_todos = None

    if hasattr(request.user, 'perfil'):
        if request.user.perfil.role == 'docente':
            cursos_asignados = (
                DocenteCurso.objects
                .filter(docente=request.user)
                .select_related('curso')
            )
        elif request.user.perfil.role == 'utp':
            cursos_todos = Curso.objects.all().select_related('profesor_jefe')

    return render(request, 'home.html', {
        'cursos_asignados': cursos_asignados,
        'cursos_todos': cursos_todos,
    })


@login_required
def curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    return render(request, 'curso.html', {'curso': curso}) #REVISAR



#MOSTRAR SOLO ALUMNOS DE SU CURSO
@login_required
def asistencia(request, curso_id):

    curso = get_object_or_404(Curso, id=curso_id)

    alumnos = Alumno.objects.filter(curso=curso)

    return render(request, 'asistencia.html', {
        'curso': curso,
        'alumnos': alumnos
    })


#MOSTRAR SOLO ALUMNOS DE SU CURSO // REVISAR
@login_required
def notas(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    alumnos = Alumno.objects.filter(curso=curso).order_by('apellidos', 'nombres')

    # Obtener notas existentes para ese curso
    notas = Nota.objects.filter(alumno__curso=curso)

    # Crear un diccionario de notas por alumno
    notas_dict = {}
    for nota in notas:
        if nota.alumno_id not in notas_dict:
            notas_dict[nota.alumno_id] = []
        notas_dict[nota.alumno_id].append(nota)

    return render(request, "notas.html", {
        "curso": curso,
        "alumnos": alumnos,
        "notas_dict": notas_dict
    })



@login_required
def anotaciones(request):
    return render(request, 'anotaciones.html')


@login_required
def reportes(request):
    return render(request, 'reportes.html')


# -------------------------
# Autenticación
# -------------------------
class MiLoginView(LoginView):
    template_name = "login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Credenciales inválidas. Verifica tus datos.")
        return super().form_invalid(form)


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            Perfil.objects.create(user=user, role=form.cleaned_data['role'])
            messages.success(request, "¡Cuenta creada con éxito! Ya puedes ingresar.")
            auth_login(request, user)
            return redirect('home')
        messages.error(request, "Revisa los campos e intenta de nuevo.")
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})


# -------------------------
# Funciones UTP
# -------------------------
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


@user_passes_test(es_utp)
def crear_curso(request):
    if request.method == "POST":
        form = CursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso creado correctamente.")
            return redirect("cursos_lista")
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = CursoForm()
    return render(request, "crear_curso.html", {"form": form})


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


@user_passes_test(es_utp)
def cursos_lista(request):
    """Listado con relaciones prefetch para eficiencia."""
    cursos = (
        Curso.objects
        .all()
        .select_related('profesor_jefe')
        .prefetch_related('asignaturas__profesor')
    )

    docentes_por_curso = {}
    for dc in DocenteCurso.objects.select_related('docente', 'curso'):
        docentes_por_curso.setdefault(dc.curso_id, []).append(dc.docente.username)

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
