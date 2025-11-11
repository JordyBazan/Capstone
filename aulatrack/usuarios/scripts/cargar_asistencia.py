from usuarios.models import Curso, Alumno, Asistencia
from datetime import date, timedelta
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
    # === Buscar curso base ===
    curso = Curso.objects.filter(nombre__icontains="Primero", año=2025).first()
    if not curso:
        print(" No se encontró el curso 'Primero' para 2025.")
        return

    alumnos = Alumno.objects.filter(curso=curso).order_by("apellidos", "nombres")
    if not alumnos.exists():
        print(" No hay alumnos en este curso.")
        return

    print(f" Generando asistencia de los últimos 2 meses para {curso.nombre} ({alumnos.count()} alumnos)...")

    # === Parámetros de generación ===
    hoy = date.today()
    dias = 60
    estados = ["Presente", "Presente", "Presente", "Presente", "Ausente", "Justificado"]
    creadas = 0

    for i in range(dias):
        fecha = hoy - timedelta(days=i)
        # Saltar fines de semana
        if fecha.weekday() >= 5:
            continue

        for alumno in alumnos:
            estado = random.choice(estados)
            Asistencia.objects.update_or_create(
                alumno=alumno,
                curso=curso,
                fecha=fecha,
                defaults={"estado": estado}
            )
            creadas += 1

        print(f" {fecha} → registros creados para {alumnos.count()} alumnos")

    print(f"\n Asistencia generada: {creadas} registros totales para {curso.nombre}")
