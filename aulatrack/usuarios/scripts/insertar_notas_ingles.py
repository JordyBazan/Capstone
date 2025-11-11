from usuarios.models import Curso, Asignatura, Alumno, Nota
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
    curso = Curso.objects.filter(nombre__icontains="Primero", año=2025).first()
    asignatura = Asignatura.objects.filter(nombre__icontains="Inglés", curso=curso).first()

    if not curso or not asignatura:
        print(" No se encontró el curso o la asignatura.")
        return

    print(f" Cargando notas para {asignatura.nombre} - {curso.nombre}")

    # === Notas ficticias (realistas, entre 4.7 y 6.5) ===
    notas_data = {
        "Daniel Alexis Bustos Cárcamo": [5.4,5.6,5.7,5.8,5.5,5.6,5.7,5.8,5.6,5.5],
        "Ariel Patricio Báez Sepulveda": [5.0,5.2,5.1,5.3,5.0,5.4,5.2,5.3,5.1,5.2],
        "Erik Fernando Caiza Jimenez": [6.1,6.0,6.3,6.2,6.1,6.2,6.3,6.1,6.0,6.2],
        "Martina Cardonne Arris": [5.6,5.8,5.7,5.9,5.8,5.9,5.7,5.8,5.9,5.8],
        "Juan Carlos Carreño Ortega": [5.0,5.1,4.9,5.2,5.1,5.3,5.2,5.0,5.1,5.3],
        "Verónica Jacqueline Casas Piñeda": [6.3,6.2,6.1,6.4,6.3,6.2,6.4,6.3,6.1,6.2],
        "Gonzalo Alfonso Colman Garrido": [5.1,5.3,5.4,5.2,5.3,5.1,5.2,5.4,5.3,5.2],
        "Paola Andrea Correa Cifuentes": [6.0,6.1,5.9,6.2,6.1,6.0,6.1,6.2,6.0,6.1],
        "Pedro Alexis Covarrubias González": [5.6,5.4,5.5,5.7,5.6,5.5,5.4,5.6,5.7,5.5],
        "Cecilia Andrea Díaz Carrasco": [6.2,6.1,6.0,6.3,6.1,6.2,6.3,6.1,6.0,6.2],
        "Adriana Ignacia Escobar Muñoz": [5.5,5.3,5.4,5.6,5.5,5.4,5.3,5.5,5.4,5.3],
        "Dominic Valentina Espina Díaz": [6.0,5.9,6.1,6.0,6.2,6.1,6.0,6.2,6.1,6.0],
        "Paulo Andrés Espinoza Cortés": [5.0,4.9,5.1,5.0,5.2,5.0,4.9,5.1,5.0,5.2],
        "Johan Antonio Farías Lecaros": [5.4,5.5,5.3,5.6,5.4,5.3,5.5,5.4,5.3,5.6],
        "Matilde Mariela Ibáñez González": [6.1,6.0,6.2,6.1,6.0,6.2,6.1,6.0,6.1,6.2],
        "Gabriel Marcos Llanquileo Saldaña": [5.3,5.2,5.4,5.3,5.2,5.1,5.3,5.4,5.2,5.3],
        "Camila Andrea Lovera Leufuman": [6.0,6.1,5.9,6.2,6.1,6.0,6.1,6.2,6.0,6.1],
        "Roció Tabita Matamala Flores": [5.8,5.6,5.7,5.8,5.9,5.7,5.8,5.6,5.7,5.8],
        "Verónica Del Carmen Moya Gutiérrez": [5.2,5.3,5.1,5.4,5.2,5.1,5.3,5.2,5.4,5.3],
        "Genesis Andrea Olavarría Olavarría": [6.4,6.3,6.2,6.5,6.3,6.4,6.2,6.3,6.5,6.4],
        "Carlos Alberto Quezada Valderrama": [5.1,5.0,5.2,5.3,5.1,5.0,5.3,5.2,5.1,5.0],
        "Isidora Andrea Rayen Gómez": [6.0,6.1,5.9,6.2,6.1,6.0,5.9,6.1,6.2,6.0],
        "Ignacio Alejandro Riquelme Torres": [5.5,5.6,5.7,5.6,5.8,5.7,5.6,5.8,5.6,5.5],
        "Oscar Sebastián Rubio Olavarría": [5.3,5.2,5.1,5.4,5.3,5.1,5.3,5.2,5.4,5.3],
        "Matías Alonso Salgado Díaz": [5.9,5.8,6.0,5.9,6.1,6.0,5.9,6.1,6.0,5.9],
        "José Ricardo Sepúlveda González": [5.4,5.2,5.3,5.5,5.4,5.3,5.2,5.4,5.3,5.5],
        "Andrés Eduardo Silva Tobar": [6.1,6.0,6.2,6.1,6.0,6.2,6.1,6.0,6.1,6.2],
        "Tomás Jesús Villagrán Soto": [5.8,5.9,6.0,5.9,6.1,6.0,5.9,6.1,6.0,5.9],
        "Humberto Segundo Zúñiga Muñoz": [5.0,5.1,5.2,5.0,5.3,5.2,5.1,5.3,5.0,5.2],
        "Doris Magaly Álvarez Rondón": [6.2,6.3,6.1,6.4,6.3,6.2,6.4,6.3,6.1,6.2],
    }

    creadas = 0
    encontradas = 0

    for nombre_completo, notas in notas_data.items():
        alumno = None
        for a in Alumno.objects.filter(curso=curso):
            if normalize(a.nombres) in normalize(nombre_completo) and normalize(a.apellidos) in normalize(nombre_completo):
                alumno = a
                break

        if not alumno:
            print(f" Alumno no encontrado: {nombre_completo}")
            continue

        encontradas += 1
        for i, valor in enumerate(notas, start=1):
            Nota.objects.update_or_create(
                alumno=alumno,
                asignatura=asignatura,
                numero=i,
                defaults={
                    "valor": round(valor, 1),
                    "profesor": asignatura.profesor,  #  se incluye profesor
                    "evaluacion": f"Nota {i}"
                }
            )
            creadas += 1

    print(f" {creadas} notas creadas o actualizadas correctamente para {encontradas} alumnos.")
