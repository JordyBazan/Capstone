from usuarios.models import Curso, Alumno, Asistencia
from datetime import date, timedelta, datetime
import random
import unicodedata

def normalize(texto):
    """Quita acentos y pasa a minúsculas."""
    if not texto:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    ).strip()


def run():
    cursos_nombres = [
        "Primero Básico",
        "Segundo Básico",
        "Tercero Básico",
        "Cuarto Básico",
        "Quinto Básico",
        "Sexto Básico",
        "Séptimo Básico",
        "Octavo Básico",
    ]

    año = 2025
    fecha_inicio = date(2025, 3, 10)
    hoy = date.today()

    estados = (
        ["Presente"] * 10  # alta probabilidad de asistencia
        + ["Ausente"] * 1
        + ["Justificado"] * 1
    )

    total_creadas = 0

    for nombre_curso in cursos_nombres:
        curso = Curso.objects.filter(nombre__icontains=nombre_curso, año=año).first()
        if not curso:
            print(f" ⚠ No se encontró el curso '{nombre_curso}' para {año}.")
            continue

        alumnos = Alumno.objects.filter(curso=curso).order_by("apellidos", "nombres")
        if not alumnos.exists():
            print(f" ⚠ No hay alumnos en el curso {curso.nombre}.")
            continue

        print(f"\n Generando asistencia para {curso.nombre} ({alumnos.count()} alumnos) desde {fecha_inicio} hasta {hoy}...")

        fecha_actual = fecha_inicio
        creadas = 0

        while fecha_actual <= hoy:
            # Saltar fines de semana (sábado=5, domingo=6)
            if fecha_actual.weekday() < 5:
                for alumno in alumnos:
                    estado = random.choice(estados)
                    Asistencia.objects.update_or_create(
                        alumno=alumno,
                        curso=curso,
                        fecha=fecha_actual,
                        defaults={"estado": estado},
                    )
                    creadas += 1

            fecha_actual += timedelta(days=1)

        total_creadas += creadas
        print(f" {creadas} registros generados para {curso.nombre}")

    print(f"\n Asistencia generada exitosamente: {total_creadas} registros totales hasta {hoy}")
