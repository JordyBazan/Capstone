# =========================================================
# Importaciones
# =========================================================
import re
from io import BytesIO
from collections import Counter

from datetime import date
from django.contrib import messages


from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

# Modelos
from .models import Perfil, DocenteCurso, Alumno, Curso, Asignatura, Nota, Asistencia

# Formularios
from .forms import (
    RegistroForm, LoginForm,
    CursoForm, AsignaturaForm, CursoAsignaturasForm, AsignarProfesorJefeForm,CursoEditForm, AlumnoForm
)

# =========================================================
# Utilidades / Permisos
# =========================================================
def es_utp(user):
    return user.is_authenticated and hasattr(user, "perfil") and user.perfil.role == "utp"

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
# Páginas principales
# =========================================================
def home(request):
    user = request.user
    ordenar = request.GET.get("ordenar") or "basico_asc"

    cursos_docente = None
    cursos_todos = None

    # ----- DOCENTE: cursos donde es PJ, dicta una asignatura o tiene DocenteCurso
    if hasattr(user, "perfil") and user.perfil.role == "docente":
        ids = set()
        ids.update(Curso.objects.filter(profesor_jefe=user).values_list("id", flat=True))
        ids.update(Curso.objects.filter(docentecurso__docente=user).values_list("id", flat=True))
        ids.update(Curso.objects.filter(asignaturas__profesor=user).values_list("id", flat=True))

        cursos_docente = list(
            Curso.objects.filter(id__in=ids)
            .select_related("profesor_jefe")
            .prefetch_related("asignaturas")
            .distinct()
        )
        if ordenar == "basico_asc":
            cursos_docente.sort(key=lambda c: _clave_grado(c.nombre))
        elif ordenar == "basico_desc":
            cursos_docente.sort(key=lambda c: _clave_grado(c.nombre), reverse=True)
        elif ordenar == "nombre_asc":
            cursos_docente.sort(key=lambda c: (c.nombre or "").lower())

    # ----- UTP: todos los cursos
    if hasattr(user, "perfil") and user.perfil.role == "utp":
        cursos_todos = list(
            Curso.objects.all()
            .select_related("profesor_jefe")
            .prefetch_related("asignaturas")
        )
        if ordenar == "basico_asc":
            cursos_todos.sort(key=lambda c: _clave_grado(c.nombre))
        elif ordenar == "basico_desc":
            cursos_todos.sort(key=lambda c: _clave_grado(c.nombre), reverse=True)
        elif ordenar == "nombre_asc":
            cursos_todos.sort(key=lambda c: (c.nombre or "").lower())

    return render(request, "home.html", {
        "cursos_docente": cursos_docente,
        "cursos_todos": cursos_todos,
    })


@login_required
def curso(request, curso_id):
    curso = get_object_or_404(Curso.objects.select_related("profesor_jefe"), id=curso_id)
    return render(request, "curso.html", {"curso": curso})


@login_required
def asistencia(request, curso_id):
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
class MiLoginView(LoginView):
    template_name = "login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Credenciales inválidas. Verifica tus datos.")
        return super().form_invalid(form)


def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            Perfil.objects.create(user=user, role=form.cleaned_data["role"])
            messages.success(request, "¡Cuenta creada con éxito! Ya puedes ingresar.")
            auth_login(request, user)
            return redirect("home")
        messages.error(request, "Revisa los campos e intenta de nuevo.")
    else:
        form = RegistroForm()
    return render(request, "registro.html", {"form": form})


# =========================================================
# UTP - Gestión académica
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
    if request.method == "POST":
        form = AsignaturaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Asignatura creada con éxito.")
            return redirect("cursos_lista")
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsignaturaForm()
    return render(request, "crear_asignatura.html", {"form": form})


@user_passes_test(es_utp)
def cursos_lista(request):
    cursos = (
        Curso.objects
        .select_related("profesor_jefe")
        .prefetch_related("asignaturas", "asignaturas__profesor")
        .annotate(
            num_asignaturas=Count("asignaturas", distinct=True),
            num_alumnos=Count("alumno", distinct=True),   # reverse FK: Alumno.curso
        )
        .order_by("año", "nombre")
    )
    asignaturas = Asignatura.objects.all().order_by("nombre")
    docentes = User.objects.filter(perfil__role="docente").order_by("first_name", "last_name", "username")

    return render(request, "cursos_lista.html", {
        "cursos": cursos,
        "asignaturas": asignaturas,
        "docentes": docentes,
    })


@user_passes_test(es_utp)
def curso_editar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    form = CursoEditForm(request.POST or None, instance=curso)
    docentes = User.objects.filter(perfil__role='docente').order_by('first_name','last_name','username')

    if form.is_valid():
        form.save()
        messages.success(request, "Curso actualizado.")
        return redirect('cursos_lista')

    return render(request, 'curso_editar.html', {
        'curso': curso,
        'form': form,
        'docentes': docentes,
    })


@user_passes_test(es_utp)
def curso_eliminar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == "POST":
        curso.delete()
        messages.success(request, "Curso eliminado.")
        return redirect("cursos_lista")
    return render(request, "curso_eliminar_confirmar.html", {"curso": curso})


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

# =========================================================
# Crear Alumno
# =========================================================

@login_required
def agregar_alumno(request):
    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Alumno agregado correctamente.")
            return redirect('agregar_alumno')  # o 'lista_alumnos', si tienes una lista
    else:
        form = AlumnoForm()
    
    return render(request, 'agregar_alumno.html', {'form': form})









@user_passes_test(es_utp)
@require_POST
def curso_quitar_asignatura(request, curso_id, asignatura_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)
    curso.asignaturas.remove(asignatura)
    messages.success(request, f"Se quitó «{asignatura.nombre}» del curso {curso}.")
    return redirect("cursos_lista")


# =========================================================
# Asignaturas (Listar / Editar / Eliminar)
# =========================================================
@user_passes_test(es_utp)
def asignatura_list(request):
    asignaturas = Asignatura.objects.select_related("profesor").order_by("nombre")
    return render(request, "asignatura_list.html", {"asignaturas": asignaturas})


@user_passes_test(es_utp)
@transaction.atomic
def asignatura_editar(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if request.method == "POST":
        form = AsignaturaForm(request.POST, instance=asignatura)
        if form.is_valid():
            form.save()
            messages.success(request, "Asignatura actualizada correctamente.")
            return redirect("cursos_lista")
        messages.error(request, "Revisa los errores del formulario.")
    else:
        form = AsignaturaForm(instance=asignatura)
    return render(request, "asignatura_form.html", {"form": form, "modo": "editar", "asignatura": asignatura})


@user_passes_test(es_utp)
@transaction.atomic
def asignatura_eliminar(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if request.method == "POST":
        asignatura.delete()
        messages.success(request, "Asignatura eliminada.")
        return redirect("cursos_lista")
    return render(request, "confirm_delete.html", {"obj": asignatura, "tipo": "Asignatura"})


# =========================================================
# Asignar Profesor Jefe
#   - Página (con formulario AsignarProfesorJefeForm)
#   - Inline POST desde curso_editar (dropdown)
# =========================================================
@user_passes_test(es_utp)
def asignar_profesor_jefe(request):
    """Pantalla independiente para asignar PJ usando AsignarProfesorJefeForm."""
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
    messages.success(request, msg)
    return redirect("curso_editar", pk=curso.pk)


# =========================================================
# Exportación PDF (WeasyPrint si está disponible, ReportLab como fallback)
# =========================================================



@user_passes_test(es_utp)
def cursos_export_pdf(request):
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

    total_cursos = cursos.count()
    total_alumnos = sum(c.num_alumnos for c in cursos)
    total_asignaturas_matriz = sum(c.num_asignaturas for c in cursos)

    # Conteos de asignaturas
    asig_counter = Counter()
    asignaturas_sin_prof = set()
    asig_ids_unicos = set()
    for c in cursos:
        for a in c.asignaturas.all():
            asig_ids_unicos.add(a.id)
            asig_counter[a.nombre] += 1
            if not a.profesor_id:
                asignaturas_sin_prof.add(a.nombre)
    asignaturas_distintas = len(asig_ids_unicos)

    # Alertas
    cursos_sin_pj = [c for c in cursos if not c.profesor_jefe_id]
    cursos_sin_asignaturas = [c for c in cursos if c.num_asignaturas == 0]

    # Distribución por nivel
    def nivel_de(c):
        s = f"{c.año or ''} {c.nombre or ''}".lower()
        if re.search(r"bas(i|í)co", s):
            return "Básico"
        if "medio" in s:
            return "Medio"
        return "Otros"

    dist_nivel_counter = Counter(nivel_de(c) for c in cursos)
    dist_basico = dist_nivel_counter.get("Básico", 0)
    dist_medio = dist_nivel_counter.get("Medio", 0)
    dist_otros = dist_nivel_counter.get("Otros", 0)

    # Top PJs y top asignaturas
    top_pj = Counter(
        (c.profesor_jefe.get_full_name() or c.profesor_jefe.username)
        for c in cursos if c.profesor_jefe_id
    ).most_common(5)
    top_asignaturas = asig_counter.most_common(8)

    # KPIs derivados
    if total_cursos:
        pct_con_pj = round(100 * (1 - (len(cursos_sin_pj) / total_cursos)), 1)
        pct_con_asignaturas = round(100 * (1 - (len(cursos_sin_asignaturas) / total_cursos)), 1)
    else:
        pct_con_pj = 0
        pct_con_asignaturas = 0

    ctx = {
        "titulo": "Informe Ejecutivo de Cursos",
        "generado": timezone.localtime(),
        "usuario": request.user,
        "cursos": cursos,
        "total_cursos": total_cursos,
        "total_alumnos": total_alumnos,
        "total_asignaturas_matriz": total_asignaturas_matriz,
        "asignaturas_distintas": asignaturas_distintas,
        "pct_con_pj": pct_con_pj,
        "pct_con_asignaturas": pct_con_asignaturas,
        "dist_nivel": {"Básico": dist_basico, "Medio": dist_medio, "Otros": dist_otros},
        "top_pj": top_pj,
        "top_asignaturas": top_asignaturas,
        "asignaturas_sin_prof": sorted(asignaturas_sin_prof),
        "cursos_sin_pj": cursos_sin_pj,
        "cursos_sin_asignaturas": cursos_sin_asignaturas,
    }

    # Intento con WeasyPrint
    try:
        from weasyprint import HTML  # import local
        html = render_to_string("pdf/cursos_export_pdf.html", ctx)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = 'attachment; filename="informe_cursos.pdf"'
        return resp
    except Exception:
        # Fallback ReportLab
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
            ListFlowable, ListItem
        )
        from reportlab.lib.styles import getSampleStyleSheet

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=14*mm, rightMargin=14*mm, topMargin=18*mm, bottomMargin=18*mm
        )
        styles = getSampleStyleSheet()
        story = []

        title = Paragraph("<b>Informe Ejecutivo de Cursos</b>", styles["Title"])
        meta = Paragraph(
            f"Generado: {timezone.localtime().strftime('%d/%m/%Y %H:%M')} · Usuario: {request.user.get_full_name() or request.user.username}",
            styles["Normal"]
        )
        story += [title, Spacer(1, 4*mm), meta, Spacer(1, 8*mm)]

        kpi_text = (
            f"<b>Total de cursos:</b> {total_cursos}  |  "
            f"<b>Total de alumnos:</b> {total_alumnos}  |  "
            f"<b>Asignaturas distintas:</b> {asignaturas_distintas}  |  "
            f"<b>Relaciones curso-asignatura:</b> {total_asignaturas_matriz}<br/>"
            f"<b>% cursos con PJ:</b> {pct_con_pj}%  |  "
            f"<b>% cursos con asignaturas:</b> {pct_con_asignaturas}%"
        )
        story += [Paragraph(kpi_text, styles["BodyText"]), Spacer(1, 6*mm)]

        data = [["Año", "Nombre", "Sala", "# Asig.", "# Alumn.", "Profesor Jefe"]]
        for c in cursos:
            pj = (c.profesor_jefe.get_full_name() or c.profesor_jefe.username) if c.profesor_jefe else "—"
            data.append([c.año, c.nombre, c.sala, c.num_asignaturas, c.num_alumnos, pj])

        table = Table(data, repeatRows=1, colWidths=[22*mm, 42*mm, 18*mm, 20*mm, 22*mm, 60*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f8fafc")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#6b7280")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("ALIGN", (3,1), (4,-1), "RIGHT"),
            ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fbfdff")]),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story += [table]

        story += [PageBreak(), Paragraph("<b>Alertas</b>", styles["Heading1"]), Spacer(1, 3*mm)]
        bullets = []
        if cursos_sin_pj:
            bullets.append(Paragraph(f"Cursos sin Profesor Jefe: {len(cursos_sin_pj)}", styles["BodyText"]))
        if cursos_sin_asignaturas:
            bullets.append(Paragraph(f"Cursos sin asignaturas: {len(cursos_sin_asignaturas)}", styles["BodyText"]))
        if asignaturas_sin_prof:
            bullets.append(Paragraph(f"Asignaturas sin profesor (al menos en un curso): {len(asignaturas_sin_prof)}", styles["BodyText"]))
        if not bullets:
            bullets.append(Paragraph("Sin alertas relevantes.", styles["BodyText"]))
        story += [ListFlowable([ListItem(b) for b in bullets], bulletType="bullet", leftIndent=12)]

        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = 'attachment; filename="informe_cursos.pdf"'
        return resp








# =========================================================
# Guardar Asistencia
# =========================================================

from datetime import date

def asistencia(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    alumnos = Alumno.objects.filter(curso=curso).order_by('apellidos', 'nombres')

    if request.method == 'POST':
        fecha_str = request.POST.get('fecha')
        if fecha_str:
            fecha = date.fromisoformat(fecha_str)
        else:
            fecha = date.today()

        for alumno in alumnos:
            estado = request.POST.get(f"estado_{alumno.id}")
            if estado:
                Asistencia.objects.update_or_create(
                    alumno=alumno,
                    curso=curso,
                    fecha=fecha,
                    defaults={'estado': estado}
                )

        messages.success(request, "Asistencia guardada correctamente.")
        return redirect('asistencia', curso_id=curso.id)

    # Filtrado por fecha (GET)
    fecha_filtrada = request.GET.get('fecha')
    if fecha_filtrada:
        asistencias = Asistencia.objects.filter(curso=curso, fecha=fecha_filtrada)
    else:
        asistencias = Asistencia.objects.filter(curso=curso, fecha=date.today())

    estados = {a.alumno.id: a.estado for a in asistencias}

    return render(request, 'asistencia.html', {
        'curso': curso,
        'alumnos': alumnos,
        'estados': estados,
        'today': date.today(),
    })



# =========================================================
# Notas
# =========================================================

from django.db.models import Avg
@login_required
def seleccionar_asignatura(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    asignaturas = Asignatura.objects.filter(curso=curso)
    context = {
        'curso': curso,
        'asignaturas': asignaturas
    }
    return render(request, 'seleccionar_asignatura.html', context)




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Curso, Asignatura, Alumno, Nota

@login_required
def libro_notas(request, curso_id, asignatura_id):
    curso = get_object_or_404(Curso, id=curso_id)
    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
    alumnos = Alumno.objects.filter(curso=curso)
    columnas_notas = range(1, 11)

    if request.method == 'POST':
        for alumno in alumnos:
            for i in columnas_notas:
                key = f'nota_{alumno.id}_{i}'
                valor = request.POST.get(key)
                if valor:
                    valor = float(valor)
                    Nota.objects.update_or_create(
                        alumno=alumno,
                        asignatura=asignatura,
                        numero=i,
                        defaults={'valor': valor, 'profesor': request.user}
                    )
        return redirect('libro_notas', curso_id=curso.id, asignatura_id=asignatura.id)

    notas_por_alumno = {}
    for alumno in alumnos:
        notas_queryset = Nota.objects.filter(alumno=alumno, asignatura=asignatura)
        notas_dict = {n.numero: n.valor for n in notas_queryset}
        notas_lista = [notas_dict.get(i, None) for i in columnas_notas]

        notas_validas = [v for v in notas_lista if v is not None]
        promedio = round(sum(notas_validas)/len(notas_validas), 1) if notas_validas else None

        notas_por_alumno[alumno] = {
            'notas': notas_lista,
            'promedio': promedio
        }

    context = {
        'curso': curso,
        'asignatura': asignatura,
        'alumnos': alumnos,
        'notas_por_alumno': notas_por_alumno,
        'columnas_notas': columnas_notas,
    }

    return render(request, 'notas.html', context)
