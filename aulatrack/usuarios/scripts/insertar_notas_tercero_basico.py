from usuarios.models import Curso, Asignatura, Alumno, Nota
import unicodedata
import random

def normalize(texto):
    if not texto:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    ).strip()

def generar_notas(curso, nombre_asignatura, rango=(4.5, 6.5)):
    """Genera notas aleatorias para una asignatura específica."""
    asignatura = Asignatura.objects.filter(nombre__icontains=nombre_asignatura, curso=curso).first()

    if not asignatura:
        print(f" No se encontró la asignatura {nombre_asignatura}.")
        return 0

    print(f" Cargando notas para {asignatura.nombre} - {curso.nombre}")

    alumnos = Alumno.objects.filter(curso=curso)
    creadas = 0

    for alumno in alumnos:
        for i in range(1, 11):
            valor = round(random.uniform(*rango), 1)
            Nota.objects.update_or_create(
                alumno=alumno,
                asignatura=asignatura,
                numero=i,
                defaults={
                    "valor": valor,
                    "profesor": asignatura.profesor,
                    "evaluacion": f"Nota {i}"
                }
            )
            creadas += 1

    print(f" {creadas} notas creadas o actualizadas correctamente ({asignatura.nombre})")
    return creadas


def run():
    curso = Curso.objects.filter(nombre__icontains="Tercero", año=2025).first()
    if not curso:
        print(" No se encontró el curso 3º Tercero Básico.")
        return

    total = 0

    # === Asignaturas de 3º Básico ===
    total += generar_notas(curso, "Ciencias Naturales", (4.6, 6.4))
    total += generar_notas(curso, "Educación Artística", (5.0, 6.8))
    total += generar_notas(curso, "Educación Física y Salud", (5.3, 6.9))
    total += generar_notas(curso, "Historia, Geografía y Ciencias Sociales", (4.4, 6.3))
    total += generar_notas(curso, "Inglés", (4.5, 6.4))
    total += generar_notas(curso, "Lenguaje y Comunicación", (4.3, 6.2))
    total += generar_notas(curso, "Matemáticas", (4.4, 6.5))
    total += generar_notas(curso, "Tecnología", (5.1, 6.7))

    print(f"\n Total general: {total} notas creadas o actualizadas correctamente para {curso.nombre} (8 asignaturas).")
