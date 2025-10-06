# views.py
# =========================================================
# Importaciones
# =========================================================
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db import transaction

# Modelos
from usuarios.models import Alumno, Curso, Asignatura, Nota
from .models import Perfil, DocenteCurso

# Formularios
from .forms import (
    RegistroForm, LoginForm, DocenteCursoForm,
    CursoEditForm, CursoForm, AsignaturaForm, CursoAsignaturasForm, AsignarProfesorJefeForm
)
from django.db.models import Q



# =========================================================
# Utilidades / Permisos
# =========================================================
def es_utp(user):
    return user.is_authenticated and hasattr(user, 'perfil') and user.perfil.role == 'utp'


# =========================================================
# Páginas principales (Dashboard / Curso / Vistas docentes)
# =========================================================
def home(request):
    cursos_asignados = None
    cursos_todos = None

    if hasattr(request.user, 'perfil'):
        role = request.user.perfil.role

        if role == 'docente':
            cursos_asignados = (
                Curso.objects.filter(
                    Q(docentecurso__docente=request.user) |
                    Q(asignaturas__profesor=request.user)
                )
                .select_related('profesor_jefe')
                .prefetch_related('asignaturas')
                .distinct()
                .order_by('nombre')
            )

        elif role == 'utp':
            cursos_todos = (
                Curso.objects
                .all()
                .select_related('profesor_jefe')
                .prefetch_related('asignaturas__profesor')
                .order_by('nombre')
            )
            cursos_asignados = (
                Curso.objects.filter(
                    Q(docentecurso__docente=request.user) |
                    Q(asignaturas__profesor=request.user)
                )
                .select_related('profesor_jefe')
                .prefetch_related('asignaturas')
                .distinct()
                .order_by('nombre')
            )

    return render(request, 'home.html', {
        'cursos_asignados': cursos_asignados,
        'cursos_todos': cursos_todos,
    })


@login_required
def curso(request, curso_id):
    curso = get_object_or_404(Curso.objects.select_related('profesor_jefe'), id=curso_id)
    return render(request, 'curso.html', {'curso': curso})


@login_required
def asistencia(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by('apellidos', 'nombres')

    return render(request, 'asistencia.html', {
        'curso': curso,
        'alumnos': alumnos
    })


@login_required
def notas(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by('apellidos', 'nombres')

    notas_qs = Nota.objects.filter(alumno__curso=curso)
    notas_dict = {}
    for nota in notas_qs:
        notas_dict.setdefault(nota.alumno_id, []).append(nota)

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


# =========================================================
# Autenticación (Login / Registro)
# =========================================================
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


# =========================================================
# Funciones de UTP (Gestión académica)
# =========================================================
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
            return redirect('cursos_lista')
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsignaturaForm()
    return render(request, 'crear_asignatura.html', {'form': form})


@user_passes_test(es_utp)
def cursos_lista(request):
    cursos = (
        Curso.objects
        .all()
        .select_related('profesor_jefe')
        .prefetch_related('asignaturas__profesor')
        .order_by('nombre')
    )

    docentes_por_curso = {}
    for dc in DocenteCurso.objects.select_related('docente', 'curso'):
        docentes_por_curso.setdefault(dc.curso_id, []).append(dc.docente.username)

    asignaturas = Asignatura.objects.select_related('profesor').all().order_by('nombre')

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
        messages.error(request, "Revisa los errores del formulario.")
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


@user_passes_test(es_utp)
def asignar_asignaturas_curso(request, curso_id):
    curso = get_object_or_404(
        Curso.objects.select_related("profesor_jefe").prefetch_related("asignaturas"),
        pk=curso_id
    )
    if request.method == "POST":
        form = CursoAsignaturasForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, f"Asignaturas actualizadas para {curso}.")
            return redirect("cursos_lista")
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = CursoAsignaturasForm(instance=curso)

    return render(request, "asignar_asignaturas_curso.html", {"curso": curso, "form": form})


@user_passes_test(es_utp)
def asignar_docente_curso(request):
    if request.method == 'POST':
        form = DocenteCursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Docente asignado correctamente al curso.")
            return redirect('cursos_lista')
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = DocenteCursoForm()

    return render(request, 'asignar_docente_curso.html', {'form': form})


# === Quitar una asignatura del curso (botón × del chip) ===
@user_passes_test(es_utp)
@require_POST
def curso_quitar_asignatura(request, curso_id, asignatura_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)

    curso.asignaturas.remove(asignatura)
    messages.success(request, f"Se quitó «{asignatura.nombre}» del curso {curso}.")
    return redirect('cursos_lista')


# =========================================================
# Asignaturas (Listar / Editar / Eliminar)
# =========================================================
@user_passes_test(es_utp)
def asignatura_list(request):
    asignaturas = Asignatura.objects.select_related('profesor').order_by('nombre')
    return render(request, 'asignatura_list.html', {'asignaturas': asignaturas})


@user_passes_test(es_utp)
@transaction.atomic
def asignatura_editar(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, instance=asignatura)
        if form.is_valid():
            form.save()
            messages.success(request, "Asignatura actualizada correctamente.")
            return redirect('cursos_lista')
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsignaturaForm(instance=asignatura)
    return render(request, 'asignatura_form.html', {'form': form, 'modo': 'editar', 'asignatura': asignatura})


@user_passes_test(es_utp)
@transaction.atomic
def asignatura_eliminar(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if request.method == 'POST':
        asignatura.delete()
        messages.success(request, "Asignatura eliminada.")
        return redirect('cursos_lista')
    return render(request, 'confirm_delete.html', {'obj': asignatura, 'tipo': 'Asignatura'})


# =========================================================
# Asignar Profesor Jefe
# =========================================================
@login_required
def asignar_profesor_jefe(request):
    if not hasattr(request.user, "perfil") or request.user.perfil.role != "utp":
        messages.error(request, "No tienes permisos para esta acción.")
        return redirect("home")

    initial_curso = None
    curso_id = request.GET.get("curso")
    if curso_id:
        initial_curso = get_object_or_404(Curso, id=curso_id)

    if request.method == "POST":
        form = AsignarProfesorJefeForm(request.POST)
        if form.is_valid():
            curso = form.cleaned_data["curso"]
            docente = form.cleaned_data["docente"]
            curso.profesor_jefe = docente
            curso.save(update_fields=["profesor_jefe"])
            messages.success(request, f"Se asignó a «{docente.username}» como profesor jefe de «{curso}».")
            return redirect("cursos_lista")
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsignarProfesorJefeForm(initial_curso=initial_curso)

    cursos = (
        Curso.objects
        .all()
        .select_related("profesor_jefe")
        .order_by("año", "nombre")
    )

    return render(request, "asignar_profesor_jefe.html", {"form": form, "cursos": cursos})
