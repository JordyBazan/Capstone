# =========================================================
# Importaciones
# =========================================================
import re
from io import BytesIO
from collections import Counter
from datetime import date

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.db.models import Q, Prefetch

#  Para registrar acciones
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

# Modelos
from .models import Alumno, Curso, Asignatura, Nota, Asistencia, Anotacion, Usuario
from django import forms

# Formularios
from .forms import (
    RegistroForm, LoginForm,
    CursoForm, AsignaturaForm, CursoAsignaturasForm, AsignarProfesorJefeForm,
    CursoEditForm, AlumnoForm, AsignarAsignaturasForm
)

# =========================================================
# Utilidades / Permisos
# =========================================================

def es_utp(user):
    #  Permite tanto al rol UTP como al superusuario
    return (hasattr(user, 'role') and user.role == 'utp') or user.is_superuser

# =========================================================
# Helper de orden por grado (1º→8º Básico, luego Medio, etc.)
# =========================================================
def _clave_grado(nombre: str):
    if not nombre:
        return (2, 99, "")
    s = nombre.lower()
    es_basico = ("básico" in s) or ("basico" in s)
    es_medio  = ("medio" in s)
    m = re.search(r"(\d+)", s)
    num = int(m.group(1)) if m else 99
    prioridad = 0 if es_basico else (1 if es_medio else 2)
    return (prioridad, num, s)

# =========================================================
#  Función genérica para registrar acciones
# =========================================================
def registrar_accion(user, objeto, tipo_accion, mensaje=""):
    """
    Registra una acción manualmente en LogEntry.
    tipo_accion: ADDITION, CHANGE o DELETION
    """
    try:
        if user is None or not getattr(user, "id", None):
            # Si no hay usuario autenticado, no registramos para evitar errores
            return
        LogEntry.objects.log_action(
            user_id=user.id,
            content_type_id=ContentType.objects.get_for_model(objeto).pk,
            object_id=getattr(objeto, "pk", None),
            object_repr=str(objeto),
            action_flag=tipo_accion,
            change_message=mensaje
        )
    except Exception as e:
        # Evitar romper el flujo por logging
        print(" Error registrando acción:", e)


# =========================================================
# Página principal (Home)
# =========================================================

@login_required
def home(request):
    user = request.user
    ordenar = request.GET.get("ordenar") or "basico_asc"

    cursos_docente = []
    cursos_todos = []
    curso_profesor_jefe = None

    # =====================================================
    # DOCENTE: solo sus cursos y asignaturas
    # =====================================================
    if getattr(user, "role", None) == "docente":
        curso_profesor_jefe = (
            Curso.objects
            .filter(profesor_jefe=user)
            .select_related("profesor_jefe")
            .prefetch_related("asignaturas", "asignaturas__profesor")
            .first()
        )

        cursos_docente = (
            Curso.objects
            .filter(asignaturas__profesor=user)
            .exclude(profesor_jefe=user)
            .select_related("profesor_jefe")
            .prefetch_related("asignaturas", "asignaturas__profesor")
            .distinct()
        )

        cursos_docente = list(cursos_docente)
        if ordenar == "basico_asc":
            cursos_docente.sort(key=lambda c: _clave_grado(c.nombre))
        elif ordenar == "basico_desc":
            cursos_docente.sort(key=lambda c: _clave_grado(c.nombre), reverse=True)
        elif ordenar == "nombre_asc":
            cursos_docente.sort(key=lambda c: (c.nombre or "").lower())

    # =====================================================
    # UTP, INSPECTOR y SUPERUSUARIO: ver todos los cursos
    # =====================================================
    elif user.is_superuser or getattr(user, "role", None) in ["utp", "inspector"]:
        cursos_todos = list(
            Curso.objects
            .select_related("profesor_jefe")
            .prefetch_related("asignaturas", "asignaturas__profesor")
        )

        if ordenar == "basico_asc":
            cursos_todos.sort(key=lambda c: _clave_grado(c.nombre))
        elif ordenar == "basico_desc":
            cursos_todos.sort(key=lambda c: _clave_grado(c.nombre), reverse=True)
        elif ordenar == "nombre_asc":
            cursos_todos.sort(key=lambda c: (c.nombre or "").lower())

    # =====================================================
    # Render
    # =====================================================
    return render(request, "home.html", {
        "curso_profesor_jefe": curso_profesor_jefe,
        "cursos_docente": cursos_docente,
        "cursos_todos": cursos_todos,
    })


@login_required
def curso(request, curso_id):
    curso = get_object_or_404(Curso.objects.select_related("profesor_jefe"), id=curso_id)
    return render(request, "curso.html", {"curso": curso})

# =========================================================
# (Versión simple de asistencia - SOLO lectura lista)
# =========================================================
@login_required
def asistencia_listado(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by("apellidos", "nombres")
    return render(request, "asistencia.html", {"curso": curso, "alumnos": alumnos})

@login_required
def notas(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by("apellidos", "nombres")
    notas_qs = Nota.objects.filter(alumno__curso=curso)
    notas_dict = {}
    for nota in notas_qs:
        notas_dict.setdefault(nota.alumno_id, []).append(nota)
    return render(request, "notas.html", {"curso": curso, "alumnos": alumnos, "notas_dict": notas_dict})

@login_required
def anotaciones(request):
    return render(request, "anotaciones.html")

@login_required
def reportes(request):
    return render(request, "reportes.html")

# =========================================================
# Autenticación (Login / Registro)
# =========================================================
from django.contrib.auth import authenticate, login, logout
from django.views.generic.edit import CreateView

class MiLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('usuarios:home_page') 

    def get_success_url(self):
        # Ignora el rol, siempre lleva al home
        messages.success(self.request, f"Bienvenido, {self.request.user.username}.")
        return self.success_url

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, "Cuenta creada correctamente. Ya puedes iniciar sesión.")
            return redirect('usuarios:login')
        else:
            print(" ERRORES DEL FORMULARIO:", form.errors)
            messages.error(request, "Revisa los campos e intenta nuevamente.")
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

def login_view(request):
    # Si ya está autenticado, ir directo al Home
    if request.user.is_authenticated:
        return redirect('usuarios:home_page')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Siempre redirigir al Home tras iniciar sesión
            return redirect('usuarios:home_page')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# =========================================================
# Cursos / Asignaturas / Usuarios - Listas principales
# =========================================================
@login_required
def cursos_lista(request):


    page = request.GET.get("page", "1")
    curso_id = request.GET.get("curso")
    filtro_nombre = request.GET.get("nombre_asignatura")

    cursos = (
        Curso.objects
        .select_related("profesor_jefe")
        .prefetch_related("asignaturas", "asignaturas__profesor")
        .annotate(
            num_asignaturas=Count("asignaturas", distinct=True),
            num_alumnos=Count("alumno", distinct=True),
        )
        .order_by("año", "nombre")
    )

    docentes = Usuario.objects.filter(role="docente").order_by("first_name", "last_name", "username")

    # ===============================
    # Página 2: Asignaturas
    # ===============================
    if page == "2":
        asignaturas_qs = (
            Asignatura.objects
            .select_related("profesor", "curso")
            .order_by("curso__nombre", "nombre")
        )

        # Filtros
        if curso_id:
            asignaturas_qs = asignaturas_qs.filter(curso_id=curso_id)

        # Si se selecciona una asignatura como "Ciencias Naturales", traer TODAS con ese nombre base
        if filtro_nombre:
            asignaturas_qs = asignaturas_qs.filter(nombre__icontains=filtro_nombre)

        # Nombres base de asignaturas (agrupadas por nombre principal sin curso)
        nombres_asignaturas = (
            Asignatura.objects
            .values_list("nombre", flat=True)
            .distinct()
        )

        # Limpiar los nombres: quitar el texto de curso, si existiera
        nombres_limpios = set()
        for nombre in nombres_asignaturas:
            base = nombre.split(" - ")[0].strip()
            nombres_limpios.add(base)
        nombres_asignaturas = sorted(nombres_limpios)

        total_asignaturas = asignaturas_qs.count()
        total_sin_profesor = asignaturas_qs.filter(profesor__isnull=True).count()
        total_con_profesor = asignaturas_qs.filter(profesor__isnull=False).count()

        resumen_por_curso = (
            Asignatura.objects
            .values("curso__nombre")
            .annotate(total=Count("id"))
            .order_by("curso__nombre")
        )

        context = {
            "page": page,
            "asignaturas": asignaturas_qs,
            "cursos": cursos,
            "curso_id": curso_id,
            "nombre_asignatura": filtro_nombre,
            "total_asignaturas": total_asignaturas,
            "total_sin_profesor": total_sin_profesor,
            "total_con_profesor": total_con_profesor,
            "resumen_por_curso": resumen_por_curso,
            "docentes": docentes,
            "nombres_asignaturas": nombres_asignaturas,
        }
        return render(request, "cursos_lista.html", context)

    # ===============================
    # Página 3: Alumnos
    # ===============================
    alumnos = (
        Alumno.objects
        .select_related("curso")
        .order_by("curso__año", "curso__nombre", "apellidos", "nombres")
    )
    if curso_id:
        alumnos = alumnos.filter(curso_id=curso_id)

    # ===============================
    # Página 1: Cursos
    # ===============================
    asignaturas = Asignatura.objects.select_related("profesor").all().order_by("nombre")

    context = {
        "page": page,
        "cursos": cursos,
        "asignaturas": asignaturas,
        "docentes": docentes,
        "alumnos": alumnos,
        "cursos_alumno": cursos,
        "curso_seleccionado": int(curso_id) if curso_id else None,
    }

    return render(request, "cursos_lista.html", context)

# =========================================================
# UTP - Gestión académica (CRUD + logging)
# =========================================================
@user_passes_test(es_utp)
def crear_curso(request):
    # Saber desde dónde viene la creación (home o cursos_lista)
    origen = request.GET.get('from') or request.POST.get('from') or ''

    if request.method == "POST":
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save()
            registrar_accion(request.user, curso, ADDITION, "Curso creado desde vista personalizada")
            messages.success(request, "Curso creado correctamente.")

            # Redirigir según el origen
            if origen == 'home':
                return redirect('usuarios:home_page')
            else:
                return redirect(f"{reverse('usuarios:cursos_lista')}?page=1")

        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = CursoForm()

    return render(request, "crear_curso.html", {
        "form": form,
        "origen": origen,  # Para mantenerlo en el form
    })

@user_passes_test(es_utp)
def curso_eliminar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)

    # Verificar desde dónde viene (home o lista)
    referer = request.META.get('HTTP_REFERER', '')
    viene_de_home = '/home' in referer or referer.endswith('/')

    if request.method == "POST" or request.method == "GET":
        registrar_accion(request.user, curso, DELETION, "Curso eliminado desde vista personalizada")
        curso.delete()
        messages.success(request, f"Curso «{curso.nombre}» eliminado correctamente.")

        # Si vino desde home → volver al home
        if viene_de_home:
            return redirect('usuarios:home_page')

        # Si vino desde lista → mantener page=1
        return redirect(f"{reverse('usuarios:cursos_lista')}?page=1")

    return render(request, "curso_eliminar_confirmar.html", {"curso": curso})



@user_passes_test(es_utp)
def curso_editar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    form = CursoEditForm(request.POST or None, instance=curso)
    docentes = Usuario.objects.filter(role=Usuario.ROLE_DOCENTE).order_by('first_name', 'last_name', 'username')

    referer = request.META.get('HTTP_REFERER', '')
    viene_de_home = '/home' in referer or referer.endswith('/')

    if form.is_valid():
        curso = form.save()
        registrar_accion(request.user, curso, CHANGE, "Curso actualizado desde vista personalizada")
        messages.success(request, "Curso actualizado correctamente.")

        # Si viene desde home → vuelve a home
        if viene_de_home:
            return redirect('usuarios:home_page')
        # Si viene desde lista → vuelve a page=1
        return redirect(f"{reverse('usuarios:cursos_lista')}?page=1")

    return render(request, 'curso_editar.html', {
        'curso': curso,
        'form': form,
        'docentes': docentes,
    })

@user_passes_test(es_utp)
def asignar_asignaturas_curso(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)

    if request.method == "POST":
        # PASO CLAVE: Pasamos 'curso=curso' también en el POST para validar
        form = AsignarAsignaturasForm(request.POST, curso=curso)
        
        if form.is_valid():
            asignaturas_seleccionadas = form.cleaned_data["asignaturas"]
            
            # 1. Lógica de ELIMINACIÓN (Cascada)
            # Identificamos las que eran de este curso pero NO están en la nueva selección
            asignaturas_a_eliminar = Asignatura.objects.filter(curso=curso).exclude(
                id__in=asignaturas_seleccionadas.values_list('id', flat=True)
            )
            
            cant_eliminadas = asignaturas_a_eliminar.count()
            # ¡Cuidado! Esto borra Notas y Asistencias asociadas.
            asignaturas_a_eliminar.delete() 

            # 2. Lógica de ASIGNACIÓN/ACTUALIZACIÓN
            # Traemos las asignaturas huérfanas al curso
            cant_actualizadas = asignaturas_seleccionadas.update(curso=curso)

            messages.success(
                request, 
                f"Proceso completado en {curso.nombre}: {cant_actualizadas} asignaturas confirmadas. "
                f"Se eliminaron {cant_eliminadas} registros desmarcados."
            )
            
            return redirect("usuarios:cursos_lista")
        else:
            messages.error(request, "Error en el formulario. Verifique los datos.")
    else:

        asignaturas_del_curso = Asignatura.objects.filter(curso=curso)
        
        form = AsignarAsignaturasForm(
            curso=curso, 
            initial={"asignaturas": asignaturas_del_curso}
        )

    asignaturas_actuales = Asignatura.objects.filter(curso=curso)


    return render(request, "asignar_asignaturas_curso.html", {
        "curso": curso,
        "form": form,
        "asignaturas_actuales": asignaturas_actuales,
    })

# =========================================================
# Crear / Editar / Eliminar Alumno
# =========================================================
@login_required
def agregar_alumno(request):
    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            alumno = form.save()
            registrar_accion(request.user, alumno, ADDITION, "Alumno creado desde vista personalizada")
            messages.success(request, "Alumno agregado correctamente.")
            return redirect(f"{reverse('usuarios:cursos_lista')}?page=3")
        else:
            messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AlumnoForm()
    return render(request, 'agregar_alumno.html', {'form': form})


@user_passes_test(es_utp)
def editar_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    cursos = Curso.objects.all().order_by('año', 'nombre')

    if request.method == 'POST':
        alumno.rut = request.POST.get('rut')
        alumno.nombres = request.POST.get('nombres')
        alumno.apellidos = request.POST.get('apellidos')
        curso_id = request.POST.get('curso')
        alumno.curso = Curso.objects.get(pk=curso_id) if curso_id else None
        alumno.save()
        registrar_accion(request.user, alumno, CHANGE, "Alumno editado desde vista personalizada")
        messages.success(request, f'Alumno {alumno.nombres} actualizado correctamente.')
        return redirect(f"{reverse('usuarios:cursos_lista')}?page=3")
    return render(request, 'editar_alumno.html', {'alumno': alumno, 'cursos': cursos})


@login_required
def eliminar_alumno(request, id):
    alumno = get_object_or_404(Alumno, id=id)
    if request.method in ["POST", "GET"]:
        registrar_accion(request.user, alumno, DELETION, "Alumno eliminado desde vista personalizada")
        alumno.delete()
        messages.success(request, "Alumno eliminado correctamente.")
        return redirect(f"{reverse('usuarios:cursos_lista')}?page=3")

# =========================================================
# Asignar Profesor Jefe (pantalla + inline)
# =========================================================
@user_passes_test(es_utp)
def asignar_profesor_jefe(request):
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
            registrar_accion(request.user, curso, CHANGE, f"Profesor Jefe asignado: {docente.get_full_name() or docente.username}")
            messages.success(request, f"Se asignó a «{docente.username}» como profesor jefe de «{curso}».")
            return redirect("usuarios:cursos_lista")  #  corregido
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsignarProfesorJefeForm(initial_curso=initial_curso)

    cursos = Curso.objects.select_related("profesor_jefe").order_by("año", "nombre")
    return render(request, "asignar_profesor_jefe.html", {"form": form, "cursos": cursos})

@require_POST
@login_required
@user_passes_test(es_utp)
def asignar_profesor_jefe_inline(request):
    """POST inline desde la pantalla de edición de curso (dropdown)."""
    curso_id = request.POST.get("curso_id")
    pj_id = request.POST.get("profesor_jefe")  # vacío => limpiar

    curso = get_object_or_404(Curso, pk=curso_id)
    if pj_id:
        docente = get_object_or_404(User, pk=pj_id, perfil__role="docente")
        curso.profesor_jefe = docente
        msg = f"Profesor Jefe asignado: {docente.get_full_name() or docente.username}"
    else:
        curso.profesor_jefe = None
        msg = "Profesor Jefe eliminado."

    curso.save(update_fields=["profesor_jefe"])
    registrar_accion(request.user, curso, CHANGE, msg)
    messages.success(request, msg)
    return redirect("curso_editar", pk=curso.pk)

# =========================================================
# Asignaturas (Listar / Editar / Eliminar)
# =========================================================
@user_passes_test(es_utp)
def asignatura_list(request):
    asignaturas = Asignatura.objects.select_related("profesor").order_by("nombre")
    return render(request, "asignatura_list.html", {"asignaturas": asignaturas})



@user_passes_test(es_utp)
def crear_asignatura(request):
    if request.method == "POST":
        form = AsignaturaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Asignatura creada correctamente.")
            return redirect(f"{reverse('usuarios:cursos_lista')}?page=2")
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsignaturaForm()
    return render(request, "crear_asignatura.html", {"form": form})


@user_passes_test(es_utp)
@transaction.atomic
def asignatura_editar(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if request.method == "POST":
        form = AsignaturaForm(request.POST, instance=asignatura)
        if form.is_valid():
            asignatura = form.save()
            registrar_accion(request.user, asignatura, CHANGE, "Asignatura actualizada desde vista personalizada")
            messages.success(request, "Asignatura actualizada correctamente.")
            return redirect(f"{reverse('usuarios:cursos_lista')}?page=2")
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsignaturaForm(instance=asignatura)
    return render(request, "asignatura_form.html", {"form": form, "modo": "editar", "asignatura": asignatura})


@user_passes_test(es_utp)
@transaction.atomic
def asignatura_eliminar(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if request.method == "POST":
        registrar_accion(request.user, asignatura, DELETION, "Asignatura eliminada desde vista personalizada")
        asignatura.delete()
        messages.success(request, "Asignatura eliminada.")
        return redirect(f"{reverse('usuarios:cursos_lista')}?page=2")
    return render(request, "confirm_delete.html", {"obj": asignatura, "tipo": "Asignatura"})





import math
# =========================================================
# Función de redondeo personalizado
# =========================================================
def redondear_personalizado(valor):
    """
    Regla especial:
    - x.5 → redondea hacia arriba
    - x.4 → redondea hacia abajo
    - resto → round normal
    Siempre entrega 1 decimal.
    """
    if valor is None:
        return None

    decimal = valor % 1

    if abs(decimal - 0.5) < 0.001:
        return math.ceil(valor * 10) / 10

    if abs(decimal - 0.4) < 0.001:
        return math.floor(valor * 10) / 10

    return round(valor, 1)


def formatear_punto_1_decimal(valor):
    """
    Aplica redondeo personalizado y devuelve string con 1 decimal usando punto.
    Ej: 5.8
    """
    if valor is None:
        return ""

    valor = redondear_personalizado(valor)
    return f"{valor:.1f}"        


# =========================================================
# Reporte de Alumno (PDF)
# =========================================================
def reporte_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    curso = alumno.curso

    from django.db.models import Avg

    # ============================
    # PROMEDIOS IGUAL QUE EL HTML
    # ============================
    qs_prom = (
        Nota.objects.filter(alumno=alumno)
        .values("asignatura__nombre", "asignatura_id")
        .annotate(promedio=Avg("valor"))
        .order_by("asignatura__nombre")
    )

    asignaturas_data = []

    for item in qs_prom:
        asignatura_id = item["asignatura_id"]
        nombre = item["asignatura__nombre"]

        notas_qs = Nota.objects.filter(alumno=alumno, asignatura_id=asignatura_id)

        notas = [formatear_punto_1_decimal(n.valor) for n in notas_qs]

        promedio_asig = formatear_punto_1_decimal(item["promedio"])

        asignaturas_data.append({
            "nombre": nombre,
            "notas": notas,
            "promedio": promedio_asig,
        })

    # ============================
    # PROMEDIO GENERAL
    # ============================
    promedios_validos = [a["promedio"] for a in asignaturas_data if a["promedio"] not in ("", None)]

    if promedios_validos:
        prom_float = [float(p) for p in promedios_validos]
        promedio_general_val = sum(prom_float) / len(prom_float)
        promedio_general = formatear_punto_1_decimal(promedio_general_val)
    else:
        promedio_general = "0.0"

    # ============================
    # ASISTENCIA
    # ============================
    total_asistencias = Asistencia.objects.filter(alumno=alumno).count()
    presentes = Asistencia.objects.filter(alumno=alumno, estado="presente").count()
    porcentaje_asistencia = round((presentes / total_asistencias * 100), 1) if total_asistencias > 0 else 0

    # ============================
    # ANOTACIONES
    # ============================
    anotaciones = Anotacion.objects.filter(alumno=alumno).order_by("-fecha")

    # ============================
    # PDF
    # ============================
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=18*mm, bottomMargin=18*mm
    )
    styles = getSampleStyleSheet()
    story = []

    # ENCABEZADO
    story.append(Paragraph("<b>Informe Académico del Alumno</b>", styles["Title"]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Alumno:</b> {alumno.nombres} {alumno.apellidos}", styles["Normal"]))
    story.append(Paragraph(f"<b>Curso:</b> {curso.nombre}", styles["Normal"]))
    story.append(Paragraph(f"<b>RUT:</b> {alumno.rut}", styles["Normal"]))
    story.append(Paragraph(f"<b>Fecha de generación:</b> {timezone.localtime().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 6*mm))

    # TABLA DE NOTAS
    encabezados = ["Asignatura"] + [f"N{i}" for i in range(1, 11)] + ["Prom."]
    data = [encabezados]

    cell_style = ParagraphStyle("Cell", fontName="Helvetica", fontSize=10, alignment=1)

    for a in asignaturas_data:
        fila = [Paragraph(a["nombre"].upper(), cell_style)]

        # Notas
        for n_str in a["notas"]:
            if n_str == "":
                fila.append(Paragraph("", cell_style))
            else:
                valor = float(n_str)
                color = "#ff0000" if valor < 4 else "#008000"
                fila.append(Paragraph(f"<font color='{color}'>{n_str}</font>", cell_style))

        faltantes = 10 - len(a["notas"])
        for _ in range(faltantes):
            fila.append(Paragraph("", cell_style))

        prom = a["promedio"]
        if prom != "":
            valor = float(prom)
            color = "#ff0000" if valor < 4 else "#008000"
            fila.append(Paragraph(f"<b><font color='{color}'>{prom}</font></b>", cell_style))
        else:
            fila.append(Paragraph("", cell_style))

        data.append(fila)

    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.25, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f0f0")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
    ]))

    story.append(tabla)

    # PROMEDIO FINAL
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(f"<b>Promedio final del alumno:</b> {promedio_general}", styles["Normal"]))
    story.append(Paragraph(f"<b>Porcentaje de asistencia:</b> {porcentaje_asistencia}%", styles["Normal"]))
    story.append(Spacer(1, 8*mm))

    # ANOTACIONES
    story.append(Paragraph("<b>Anotaciones registradas:</b>", styles["Heading3"]))
    if anotaciones:
        for an in anotaciones:
            prof = an.profesor.get_full_name() or an.profesor.username
            story.append(Paragraph(
                f"<b>{an.fecha.strftime('%d/%m/%Y')}:</b> {an.texto} <i>({prof})</i>",
                styles["Normal"]
            ))
    else:
        story.append(Paragraph("No hay anotaciones registradas.", styles["Normal"]))
    story.append(Spacer(1, 15*mm))

    # FIRMAS
    firma_data = [
        ["__________________________", "__________________________"],
        ["Firma Apoderado(a)", "Firma Docente / UTP"]
    ]
    from reportlab.platypus import Table
    firma_table = Table(firma_data, colWidths=[90*mm, 90*mm])
    firma_table.setStyle(TableStyle([
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(firma_table)

    # PIE
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        f"<font size='9'>Documento generado automáticamente por AulaTrack el {timezone.localtime().strftime('%d/%m/%Y %H:%M')}.</font>",
        styles["Normal"]
    ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()

    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename=\"reporte_{alumno.nombres}_{alumno.apellidos}.pdf\"'
    return resp





# =========================================================
# Guardar Asistencia (CON REGISTRO)
# =========================================================
@login_required
def asistencia(request, curso_id):
    from datetime import date
    from itertools import groupby
    from operator import attrgetter

    curso = get_object_or_404(Curso, id=curso_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by('apellidos', 'nombres')
    page = request.GET.get('page', '1')

    # ================================
    # PAGE 1 - Registrar / Editar asistencia
    # ================================
    if page == "1":
        if request.method == 'POST':
            fecha_str = request.POST.get('fecha')
            fecha = date.fromisoformat(fecha_str) if fecha_str else date.today()
            cambios = 0

            for alumno in alumnos:
                estado = request.POST.get(f"estado_{alumno.id}")
                if estado:
                    Asistencia.objects.update_or_create(
                        alumno=alumno,
                        curso=curso,
                        fecha=fecha,
                        defaults={'estado': estado},
                    )
                    cambios += 1

            messages.success(request, f"Asistencia guardada correctamente ({cambios} registros).")
            return redirect(f"{reverse('usuarios:asistencia', args=[curso.id])}?page=1&fecha={fecha.isoformat()}")

        # GET → cargar asistencia de la fecha o de hoy
        fecha_filtrada = request.GET.get('fecha') or date.today().isoformat()
        asistencias = Asistencia.objects.filter(curso=curso, fecha=fecha_filtrada)
        estados = {a.alumno.id: a.estado for a in asistencias}

        return render(request, 'asistencia.html', {
            'curso': curso,
            'alumnos': alumnos,
            'estados': estados,
            'fecha_filtrada': fecha_filtrada,
            'page': '1',
        })

    # ================================
    # PAGE 2 - Histórico
    # ================================
    elif page == "2":
        fecha_filtrada = request.GET.get('fecha')

        asistencias_qs = (
            Asistencia.objects
            .filter(curso=curso)
            .select_related('alumno')
            .order_by('-fecha', 'alumno__apellidos')
        )

        if fecha_filtrada:
            asistencias_qs = asistencias_qs.filter(fecha=fecha_filtrada)

        asistencia_por_dia = []
        for fecha, registros in groupby(asistencias_qs, key=attrgetter('fecha')):
            registros = list(registros)
            total = len(registros)
            presentes = sum(1 for a in registros if a.estado.lower() == "presente")
            porcentaje = round((presentes / total) * 100, 1) if total > 0 else 0
            asistencia_por_dia.append({
                'fecha': fecha,
                'registros': registros,
                'total': total,
                'presentes': presentes,
                'porcentaje': porcentaje,
            })

        return render(request, 'asistencia_historico.html', {
            'curso': curso,
            'asistencia_por_dia': asistencia_por_dia,
            'fecha_filtrada': fecha_filtrada,
            'page': '2',
        })

# =========================================================
# Notas (CON REGISTRO)
# =========================================================
@login_required
def seleccionar_asignatura(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Caso 1: UTP o Superusuario -> puede ver TODAS las asignaturas del curso
    if getattr(request.user, "role", None) == "utp" or request.user.is_superuser:
        asignaturas = Asignatura.objects.filter(curso=curso).order_by("nombre")

    # Caso 2: Docente -> puede ver todas si es profesor jefe de este curso
    elif getattr(request.user, "role", None) == "docente":
        if curso.profesor_jefe == request.user:
            # Es profesor jefe, ve todas las asignaturas del curso
            asignaturas = Asignatura.objects.filter(curso=curso).order_by("nombre")
        else:
            # No es profesor jefe, ve solo las que él imparte
            asignaturas = Asignatura.objects.filter(
                curso=curso,
                profesor=request.user
            ).order_by("nombre")

    # Caso 3: Otros roles (por seguridad)
    else:
        asignaturas = Asignatura.objects.none()

    context = {
        "curso": curso,
        "asignaturas": asignaturas,
    }
    return render(request, "seleccionar_asignatura.html", context)



@login_required
def libro_notas(request, curso_id, asignatura_id):
    # ===========================
    # Datos base
    # ===========================
    curso = get_object_or_404(Curso, id=curso_id)
    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by("apellidos", "nombres")
    columnas_notas = range(1, 11)

    # ===========================
    # Validación de permisos
    # ===========================
    puede_editar = (
        request.user.role == "docente"
        and asignatura.profesor_id == request.user.id
    ) or request.user.role in ["utp"] or request.user.is_superuser

    # ===========================
    # Guardar notas
    # ===========================
    if request.method == "POST":
        if not puede_editar:
            messages.error(request, "No tienes permisos para modificar estas notas.")
            return redirect("usuarios:libro_notas", curso_id=curso.id, asignatura_id=asignatura.id)

        cambios = 0
        cambios_detalle = []

        for alumno in alumnos:
            for i in columnas_notas:
                key = f"nota_{alumno.id}_{i}"
                valor = request.POST.get(key)

                if valor:
                    #  Normalizar valor (coma → punto, eliminar espacios)
                    valor = valor.replace(',', '.').strip()
                    try:
                        valor = float(valor)
                    except ValueError:
                        continue

                    #  Validar rango permitido
                    if valor < 1.0 or valor > 7.0:
                        continue

                    #  Redondear a un decimal
                    valor = round(valor, 1)

                    #  Crear o actualizar la nota
                    nota, created = Nota.objects.update_or_create(
                        alumno=alumno,
                        asignatura=asignatura,
                        numero=i,
                        defaults={
                            "valor": valor,
                            "profesor": request.user,
                            "evaluacion": f"Nota {i}",
                        },
                    )

                    cambios += 1
                    cambios_detalle.append(
                        f"{'Creada' if created else 'Actualizada'} Nota {i}: {valor:.1f} "
                        f"para {alumno.nombres} {alumno.apellidos}"
                    )

        # Registrar acción consolidada
        if cambios > 0:
            registrar_accion(
                request.user,
                asignatura,
                CHANGE,
                f"Modificación de notas en {curso.nombre} - {asignatura.nombre}: {cambios} cambios.\n"
                + "\n".join(cambios_detalle[:10])
            )
            messages.success(request, f"{cambios} notas guardadas correctamente.")
        else:
            messages.info(request, "No se realizaron cambios en las notas.")

        return redirect("usuarios:libro_notas", curso_id=curso.id, asignatura_id=asignatura.id)

    # ===========================
    # Mostrar notas
    # ===========================
    notas_por_alumno = {}
    for alumno in alumnos:
        notas_queryset = Nota.objects.filter(alumno=alumno, asignatura=asignatura).order_by("numero")
        notas_dict = {n.numero: n for n in notas_queryset}

        notas_lista = [notas_dict.get(i, None) for i in columnas_notas]
        valores = [n.valor for n in notas_lista if n and n.valor is not None]
        promedio = round(sum(valores) / len(valores), 1) if valores else None

        notas_por_alumno[alumno] = {
            "notas": notas_lista,
            "promedio": promedio,
        }

    # ===========================
    # Contexto
    # ===========================
    context = {
        "curso": curso,
        "asignatura": asignatura,
        "alumnos": alumnos,
        "notas_por_alumno": notas_por_alumno,
        "columnas_notas": columnas_notas,
        "puede_editar": puede_editar,
    }

    return render(request, "notas.html", context)


# =========================================================
# Anotaciones (CON REGISTRO)
# =========================================================
@login_required
def eliminar_anotacion(request, anotacion_id):
    anotacion = get_object_or_404(Anotacion, id=anotacion_id)
    alumno_id = anotacion.alumno.id  # Guardamos el ID para volver
    
 

    if request.method == "POST":
        registrar_accion(request.user, anotacion, DELETION, "Anotación eliminada.")
        anotacion.delete()
        messages.success(request, "Anotación eliminada correctamente.")
    
    return redirect("usuarios:anotaciones_alumno", alumno_id=alumno_id)

@login_required
def anotaciones_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by('apellidos', 'nombres')
    return render(request, 'anotaciones_lista.html', {'curso': curso, 'alumnos': alumnos})

@login_required
def anotaciones_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    curso = alumno.curso

    # Importaciones necesarias para cálculos
    from django.db.models import Avg, Count, Min, Max

    # ======================================
    # 1. PROMEDIOS POR ASIGNATURA
    # ======================================
    qs_prom = (
        Nota.objects.filter(alumno=alumno)
        .values("asignatura__nombre", "asignatura_id")
        .annotate(promedio=Avg("valor"))
        .order_by("asignatura__nombre")
    )

    promedios_asignaturas = [
        {
            "asignatura__nombre": item["asignatura__nombre"],
            "promedio": redondear_personalizado(item["promedio"]),
        }
        for item in qs_prom
    ]

    # ======================================
    # 2. PROMEDIO GENERAL
    # ======================================
    proms = [p["promedio"] for p in promedios_asignaturas if p["promedio"] is not None]

    if proms:
        promedio_general_val = sum(proms) / len(proms)
        promedio = redondear_personalizado(promedio_general_val)
    else:
        promedio = 0.0

    # ======================================
    # 3. ASISTENCIA (Lógica Mejorada)
    # ======================================
    qs_asistencia = Asistencia.objects.filter(alumno=alumno)
    
    # A. Totales y Rango de Fechas (Nuevo)
    datos_agregados = qs_asistencia.aggregate(
        total=Count('id'),
        inicio=Min('fecha'),
        fin=Max('fecha')
    )
    
    total_asistencias = datos_agregados['total']
    inicio_asistencia = datos_agregados['inicio']
    fin_asistencia = datos_agregados['fin']

    # B. Desglose por estado (Presente, Ausente, Justificado)
    # Usamos un diccionario para normalizar mayúsculas/minúsculas
    contador = {
        "presente": 0,
        "ausente": 0,
        "justificado": 0,
    }

    # Agrupamos por estado para eficiencia
    resumen_asistencia = (
        qs_asistencia
        .values("estado")
        .annotate(cant=Count("id"))
    )

    for item in resumen_asistencia:
        # Convertimos a minúscula para asegurar coincidencia
        estado_key = item["estado"].lower()
        if estado_key in contador:
            contador[estado_key] = item["cant"]

    # Asignación a variables finales
    pres = contador["presente"]
    aus = contador["ausente"]
    jus = contador["justificado"]

    # Calculamos porcentaje solo sobre el total registrado
    porcentaje_asistencia = round((pres / total_asistencias * 100), 1) if total_asistencias > 0 else 0
    
    # Total de días hábiles contabilizados
    total_dias = pres + aus + jus

    # ======================================
    # 4. ANOTACIONES
    # ======================================
    anotaciones = Anotacion.objects.filter(alumno=alumno).order_by("-fecha")

    # ======================================
    # 5. CREAR ANOTACIÓN (POST)
    # ======================================
    if request.method == "POST":
        texto = request.POST.get("texto")
        if texto:
            anota = Anotacion.objects.create(
                texto=texto,
                alumno=alumno,
                profesor=request.user,
            )
            registrar_accion(request.user, anota, ADDITION, "Anotación creada.")
            messages.success(request, "Anotación agregada correctamente.")
            return redirect("usuarios:anotaciones_alumno", alumno_id=alumno.id)

    # ======================================
    # 6. RENDER
    # ======================================
    return render(
        request,
        "anotaciones.html",
        {
            # Datos básicos
            "alumno": alumno,
            "curso": curso,
            
            # Académico
            "promedio": promedio,
            "promedios_asignaturas": promedios_asignaturas,
            "anotaciones": anotaciones,
            
            # Asistencia (Datos depurados)
            "porcentaje_asistencia": porcentaje_asistencia,
            "pres": pres,
            "aus": aus,
            "jus": jus,
            "total_dias": total_dias,
            
            # Nuevos datos de rango
            "inicio_asistencia": inicio_asistencia,
            "fin_asistencia": fin_asistencia,
        },
    )


# =========================================================
# Gestión de Usuarios (UTP)
# =========================================================
def gestion_usuario(request):


    rol_seleccionado = request.GET.get('rol', '')

    usuarios_filtrados = Usuario.objects.all().order_by('nombres', 'apellidos')
    if rol_seleccionado:
        usuarios_filtrados = usuarios_filtrados.filter(role=rol_seleccionado)

    roles = Usuario.ROLE_CHOICES

    context = {
        'usuarios_filtrados': usuarios_filtrados,
        'roles': roles,
        'rol_seleccionado': rol_seleccionado,
    }
    return render(request, "gestion_usuario.html", context)

def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    # Evitar editar el superusuario si no eres tú mismo (o bloquearlo totalmente)
    if usuario.is_superuser:
        messages.warning(request, "No puedes editar al usuario administrador principal.")
        return redirect('usuarios:gestion_usuario')

    roles = Usuario.ROLE_CHOICES

    if request.method == 'POST':
        # --- NUEVO: Capturar el username ---
        nuevo_username = request.POST.get('username')
        
        # Validación simple: Verificar que el username no esté ocupado por OTRO usuario
        if Usuario.objects.filter(username=nuevo_username).exclude(pk=usuario.pk).exists():
            messages.error(request, f"El nombre de usuario '{nuevo_username}' ya está en uso.")
        else:
            usuario.username = nuevo_username
            usuario.nombres = request.POST.get('nombres')
            usuario.apellidos = request.POST.get('apellidos')
            usuario.email = request.POST.get('email')
            usuario.rut = request.POST.get('rut')

            nuevo_role = request.POST.get('role')
            if nuevo_role in dict(roles):
                usuario.role = nuevo_role

            usuario.save()
            registrar_accion(request.user, usuario, CHANGE, "Usuario editado (incluyendo username)")
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect('usuarios:gestion_usuario')

    return render(request, 'editar_usuario.html', {'usuario': usuario, 'roles': roles})

def eliminar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    #  Bloquear eliminación del superusuario
    if usuario.is_superuser:
        messages.warning(request, " No puedes eliminar al usuario administrador del sistema.")
        return redirect('usuarios:gestion_usuario')

    if request.method in ["POST", "GET"]:
        registrar_accion(request.user, usuario, DELETION, "Usuario eliminado desde vista personalizada")
        usuario.delete()
        messages.success(request, f"Usuario {usuario.username} eliminado correctamente.")
        return redirect('usuarios:gestion_usuario')


# =========================================================
# Historial de Acciones (Admin Log)
# =========================================================
@user_passes_test(es_utp)
def historial_acciones_admin(request):
    """Historial completo de todas las acciones sin paginación, con columnas alineadas."""
    import io
    from django.template.loader import render_to_string
    from django.utils import timezone
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm

    logs = (
        LogEntry.objects.select_related("user", "content_type")
        .order_by("-action_time")
    )

    accion = request.GET.get("accion")
    usuario_id = request.GET.get("usuario")
    modelo = request.GET.get("modelo")

    if accion:
        logs = logs.filter(action_flag=int(accion))
    if usuario_id:
        logs = logs.filter(user_id=usuario_id)
    if modelo:
        logs = logs.filter(content_type__model=modelo.lower())

    if "pdf" in request.GET:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()
        style_normal = ParagraphStyle(
            "normal",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#111827"),
        )
        style_accion = ParagraphStyle(
            "accion",
            fontSize=8,
            leading=10,
            alignment=1,  # centrado
        )

        story = []
        story.append(Paragraph("<b>Historial de Acciones - AulaTrack</b>", styles["Title"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Generado por:</b> {request.user.get_full_name() or request.user.username}", styles["Normal"]))
        story.append(Paragraph(f"<b>Fecha:</b> {timezone.localtime().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 10))

        data = [["Fecha", "Usuario", "Acción", "Modelo", "Objeto", "Detalle"]]

        for log in logs:
            if log.action_flag == 1:
                accion_str = "<font color='#16a34a'><b>Creación</b></font>"
            elif log.action_flag == 2:
                accion_str = "<font color='#2563eb'><b>Edición</b></font>"
            elif log.action_flag == 3:
                accion_str = "<font color='#dc2626'><b>Eliminación</b></font>"
            else:
                accion_str = "<font color='#6b7280'><b>Otro</b></font>"

            detalle = log.change_message or "—"
            detalle = detalle.replace("\n", "<br/>• ")
            detalle = f"<font color='#334155'>• {detalle}</font>"

            data.append([
                Paragraph(log.action_time.strftime("%d/%m/%Y %H:%M"), style_normal),
                Paragraph(log.user.get_full_name() or log.user.username, style_normal),
                Paragraph(accion_str, style_accion),
                Paragraph(log.content_type.model.capitalize(), style_normal),
                Paragraph(log.object_repr or "—", style_normal),
                Paragraph(detalle, style_normal),
            ])

        #  Ajuste de anchos balanceados
        table = Table(
            data,
            repeatRows=1,
            colWidths=[25 * mm, 30 * mm, 25 * mm, 35 * mm, 55 * mm, 110 * mm],
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        story.append(table)
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="Historial_AulaTrack.pdf"'
        return response

    usuarios = Usuario.objects.all().order_by("first_name", "last_name")
    modelos = (
        ContentType.objects.values_list("model", flat=True)
        .distinct()
        .order_by("model")
    )

    return render(request, "historial_admin.html", {
        "logs": logs,
        "usuarios": usuarios,
        "modelos": modelos,
        "accion_filtrada": accion,
        "usuario_filtrado": int(usuario_id) if usuario_id else None,
        "modelo_filtrado": modelo,
    })



@user_passes_test(es_utp)
def eliminar_log(request, log_id):
    """Elimina un registro específico del historial."""
    log = get_object_or_404(LogEntry, id=log_id)
    if request.method == "POST":
        log.delete()
        messages.success(request, " Registro eliminado correctamente.")
    return redirect("usuarios:historial_admin")


@user_passes_test(es_utp)
def eliminar_todos_logs(request):
    """Elimina todos los registros del historial."""
    if request.method == "POST":
        LogEntry.objects.all().delete()
        messages.success(request, "🧹 Se ha eliminado todo el historial de acciones.")
    return redirect("usuarios:historial_admin")





@user_passes_test(es_utp)
@require_POST
def curso_quitar_asignatura(request, curso_id, asignatura_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)

    # Verificar si realmente pertenece al curso
    if asignatura.curso_id != curso.id:
        messages.error(request, f"La asignatura «{asignatura.nombre}» no pertenece al curso {curso}.")
        return redirect("usuarios:cursos_lista")

    # Desvincular la asignatura
    asignatura.curso = None
    asignatura.save(update_fields=["curso"])

    messages.success(request, f"Se quitó «{asignatura.nombre}» del curso {curso}.")
    return redirect("usuarios:cursos_lista")



from .forms import AsignarDocenteCursoForm
from .models import DocenteCurso

@user_passes_test(es_utp)
def asignar_docente_curso(request):
    """Asigna un docente a un curso específico"""
    if request.method == "POST":
        form = AsignarDocenteCursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, " Docente asignado correctamente al curso.")
            return redirect("usuarios:asignar_docente_curso")
        else:
            messages.error(request, " Ocurrió un error al asignar docente. Revisa los campos.")
    else:
        form = AsignarDocenteCursoForm()

    #  Lista de docentes con cursos y sus asignaturas
    asignaciones = (
        DocenteCurso.objects
        .select_related('docente', 'curso')
        .prefetch_related('curso__asignaturas')  # importante para ver sus asignaturas
        .order_by('docente__apellidos', 'docente__nombres', 'curso__nombre')
    )

    return render(
        request,
        "asignar_docente_curso.html",
        {"form": form, "asignaciones": asignaciones},
    )

@login_required
def asignar_docente_global(request):
    """Asigna un docente a todas las asignaturas que contengan el mismo nombre base (por ejemplo, 'Ciencias Naturales')."""


    if request.method == "POST":
        nombre_asignatura = request.POST.get("nombre_asignatura")
        docente_id = request.POST.get("docente_id")

        if not nombre_asignatura or not docente_id:
            messages.error(request, "Debes seleccionar una asignatura y un docente.")
            return redirect("/cursos/?page=2")

        try:
            docente = Usuario.objects.get(id=docente_id, role="docente")
        except Usuario.DoesNotExist:
            messages.error(request, "El docente seleccionado no existe.")
            return redirect("/cursos/?page=2")

        # Buscar todas las asignaturas que contengan el nombre base (sin importar el curso)
        asignaturas_afectadas = Asignatura.objects.filter(nombre__icontains=nombre_asignatura)
        total = asignaturas_afectadas.count()

        if total == 0:
            messages.warning(request, f"No se encontraron asignaturas que coincidan con '{nombre_asignatura}'.")
            return redirect("/cursos/?page=2")

        # Actualizar en bloque
        asignaturas_afectadas.update(profesor=docente)

        messages.success(
            request,
            f"Se asignó correctamente a {docente.get_full_name() or docente.username} "
            f"como profesor de todas las asignaturas que contienen '{nombre_asignatura}' "
            f"({total} asignaturas actualizadas)."
        )

    return redirect("/cursos/?page=2")


@login_required
def eliminar_asignacion(request, asignacion_id):
    """Elimina una asignación DocenteCurso."""


    asignacion = get_object_or_404(DocenteCurso, id=asignacion_id)

    if request.method == "POST":
        nombre_docente = asignacion.docente.get_full_name() or asignacion.docente.username
        nombre_curso = asignacion.curso.nombre
        asignacion.delete()
        messages.success(request, f"Se eliminó la asignación de {nombre_docente} al curso {nombre_curso}.")
        return redirect("usuarios:asignar_docente_curso")

    return redirect("usuarios:asignar_docente_curso")

class CambiarPasswordForm(forms.Form):
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Nueva contraseña"})
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Confirmar contraseña"})
    )

def cambiar_password(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)

    if request.method == "POST":
        form = CambiarPasswordForm(request.POST)
        if form.is_valid():
            p1 = form.cleaned_data["password1"]
            p2 = form.cleaned_data["password2"]

            if p1 != p2:
                messages.error(request, "Las contraseñas no coinciden.")
            else:
                usuario.password = make_password(p1)
                usuario.save()
                messages.success(request, "Contraseña actualizada correctamente.")
                return redirect("usuarios:gestion_usuario")
    else:
        form = CambiarPasswordForm()

    return render(request, "editar_usuario.html", {
        "form_pass": form,
        "usuario": usuario,
        "modo_password": True
    })