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

def generar_notas(curso, nombre_asignatura, rango=(4.8, 6.6)):
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
    curso = Curso.objects.filter(nombre__icontains="Primero", año=2025).first()
    if not curso:
        print(" No se encontró el curso 1º Primero Básico.")
        return

    total = 0

    # Lenguaje y Comunicación
    total += generar_notas(curso, "Lenguaje", (4.7, 6.4))

    # Matemáticas
    total += generar_notas(curso, "Matemáticas", (4.8, 6.6))

    # Tecnología
    total += generar_notas(curso, "Tecnología", (5.4, 6.8))

    print(f" Total general: {total} notas creadas o actualizadas (Lenguaje + Matemáticas + Tecnología).")
