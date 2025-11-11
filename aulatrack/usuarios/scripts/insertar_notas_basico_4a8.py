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
    """Genera notas aleatorias para una asignatura de un curso específico."""
    asignatura = Asignatura.objects.filter(nombre__icontains=nombre_asignatura, curso=curso).first()

    if not asignatura:
        print(f" No se encontró la asignatura {nombre_asignatura} en {curso.nombre}")
        return 0

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

    print(f" {creadas} notas creadas o actualizadas ({asignatura.nombre}) en {curso.nombre}")
    return creadas


def generar_para_curso(nombre_curso, año, rangos):
    """Genera notas para todas las asignaturas de un curso."""
    curso = Curso.objects.filter(nombre__icontains=nombre_curso, año=año).first()
    if not curso:
        print(f" No se encontró el curso {nombre_curso} - {año}")
        return 0

    print(f"\n📘 Generando notas para {curso.nombre} ({año})")

    total = 0
    total += generar_notas(curso, "Ciencias Naturales", rangos["ciencias"])
    total += generar_notas(curso, "Educación Artística", rangos["artistica"])
    total += generar_notas(curso, "Educación Física y Salud", rangos["fisica"])
    total += generar_notas(curso, "Historia, Geografía y Ciencias Sociales", rangos["historia"])
    total += generar_notas(curso, "Inglés", rangos["ingles"])
    total += generar_notas(curso, "Lenguaje y Comunicación", rangos["lenguaje"])
    total += generar_notas(curso, "Matemáticas", rangos["matematicas"])
    total += generar_notas(curso, "Tecnología", rangos["tecnologia"])

    print(f" Total de notas creadas en {curso.nombre}: {total}")
    return total


def run():
    año = 2025

    # === Rangos personalizados según curso (para simular dificultad creciente) ===
    rangos_por_curso = {
        "Cuarto": {
            "ciencias": (4.4, 6.4),
            "artistica": (5.1, 6.8),
            "fisica": (5.4, 6.9),
            "historia": (4.3, 6.2),
            "ingles": (4.5, 6.4),
            "lenguaje": (4.2, 6.1),
            "matematicas": (4.3, 6.3),
            "tecnologia": (5.0, 6.6),
        },
        "Quinto": {
            "ciencias": (4.2, 6.3),
            "artistica": (5.0, 6.7),
            "fisica": (5.3, 6.8),
            "historia": (4.1, 6.2),
            "ingles": (4.4, 6.4),
            "lenguaje": (4.0, 6.1),
            "matematicas": (4.1, 6.2),
            "tecnologia": (4.9, 6.6),
        },
        "Sexto": {
            "ciencias": (4.0, 6.2),
            "artistica": (4.8, 6.7),
            "fisica": (5.2, 6.8),
            "historia": (4.0, 6.1),
            "ingles": (4.2, 6.3),
            "lenguaje": (4.0, 6.0),
            "matematicas": (4.0, 6.0),
            "tecnologia": (4.8, 6.5),
        },
        "Séptimo": {
            "ciencias": (3.8, 6.0),
            "artistica": (4.6, 6.6),
            "fisica": (5.0, 6.8),
            "historia": (3.9, 6.0),
            "ingles": (4.1, 6.2),
            "lenguaje": (3.8, 6.0),
            "matematicas": (3.9, 6.1),
            "tecnologia": (4.7, 6.5),
        },
        "Octavo": {
            "ciencias": (3.7, 6.0),
            "artistica": (4.5, 6.5),
            "fisica": (5.0, 6.8),
            "historia": (3.8, 5.9),
            "ingles": (4.0, 6.1),
            "lenguaje": (3.7, 5.9),
            "matematicas": (3.8, 6.0),
            "tecnologia": (4.6, 6.4),
        },
    }

    total_general = 0

    for nombre_curso, rangos in rangos_por_curso.items():
        total_general += generar_para_curso(nombre_curso, año, rangos)

    print(f"\n TOTAL GENERAL: {total_general} notas creadas o actualizadas en todos los cursos 4º a 8º Básico.")
