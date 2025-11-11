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
    asignatura = Asignatura.objects.filter(nombre__icontains="Educación Artística", curso=curso).first()

    if not curso or not asignatura:
        print(" No se encontró el curso o la asignatura.")
        return

    print(f" Cargando notas para {asignatura.nombre} - {curso.nombre}")

    # === Notas ficticias (promedios más altos, porque artística suele tener mejor rendimiento) ===
    notas_data = {
        "Daniel Alexis Bustos Cárcamo": [6.1,6.0,6.3,6.2,6.4,6.0,6.2,6.1,6.5,6.3],
        "Ariel Patricio Báez Sepulveda": [5.5,5.6,5.8,5.9,5.7,5.6,5.8,6.0,5.9,5.8],
        "Erik Fernando Caiza Jimenez": [6.4,6.5,6.3,6.2,6.4,6.5,6.6,6.3,6.2,6.4],
        "Martina Cardonne Arris": [6.2,6.1,6.0,6.3,6.2,6.1,6.3,6.2,6.1,6.4],
        "Juan Carlos Carreño Ortega": [5.7,5.5,5.8,5.9,5.6,5.8,5.7,5.9,5.8,5.6],
        "Verónica Jacqueline Casas Piñeda": [6.5,6.4,6.3,6.5,6.6,6.5,6.4,6.5,6.3,6.6],
        "Gonzalo Alfonso Colman Garrido": [5.3,5.4,5.6,5.5,5.7,5.6,5.8,5.5,5.6,5.7],
        "Paola Andrea Correa Cifuentes": [6.3,6.4,6.5,6.2,6.4,6.3,6.2,6.5,6.4,6.3],
        "Pedro Alexis Covarrubias González": [5.9,6.0,5.8,6.1,5.9,6.2,5.8,6.0,6.1,6.2],
        "Cecilia Andrea Díaz Carrasco": [6.4,6.5,6.3,6.2,6.4,6.5,6.6,6.3,6.2,6.4],
        "Adriana Ignacia Escobar Muñoz": [5.9,5.8,6.0,5.7,5.8,5.9,6.1,5.8,5.9,6.0],
        "Dominic Valentina Espina Díaz": [6.5,6.4,6.3,6.5,6.6,6.5,6.4,6.5,6.3,6.6],
        "Paulo Andrés Espinoza Cortés": [5.8,5.9,5.7,6.0,5.9,6.1,5.8,5.9,6.0,5.9],
        "Johan Antonio Farías Lecaros": [5.6,5.7,5.8,5.9,5.6,5.8,5.9,5.7,5.8,5.9],
        "Matilde Mariela Ibáñez González": [6.3,6.2,6.1,6.4,6.3,6.2,6.1,6.3,6.2,6.4],
        "Gabriel Marcos Llanquileo Saldaña": [5.9,6.0,6.1,5.8,5.9,6.0,6.1,6.2,5.9,6.0],
        "Camila Andrea Lovera Leufuman": [6.2,6.1,6.3,6.4,6.2,6.3,6.1,6.4,6.3,6.2],
        "Roció Tabita Matamala Flores": [5.7,5.8,5.9,6.0,5.8,6.1,5.9,5.8,6.0,5.9],
        "Verónica Del Carmen Moya Gutiérrez": [5.8,5.9,5.7,5.8,5.9,6.0,5.9,6.1,5.8,5.9],
        "Genesis Andrea Olavarría Olavarría": [6.5,6.4,6.3,6.5,6.6,6.5,6.4,6.5,6.3,6.6],
        "Carlos Alberto Quezada Valderrama": [5.9,6.0,6.1,6.0,6.2,6.1,6.3,6.1,6.0,6.2],
        "Isidora Andrea Rayen Gómez": [6.3,6.2,6.4,6.3,6.5,6.4,6.3,6.4,6.2,6.5],
        "Ignacio Alejandro Riquelme Torres": [6.0,5.9,6.1,6.0,6.2,6.1,6.3,6.1,6.0,6.2],
        "Oscar Sebastián Rubio Olavarría": [5.8,5.9,6.0,5.9,6.1,6.0,6.2,6.0,5.9,6.1],
        "Matías Alonso Salgado Díaz": [6.2,6.1,6.0,6.3,6.2,6.1,6.3,6.4,6.2,6.1],
        "José Ricardo Sepúlveda González": [5.7,5.9,5.8,5.7,5.9,6.0,5.9,6.1,5.8,5.9],
        "Andrés Eduardo Silva Tobar": [6.3,6.2,6.1,6.4,6.3,6.2,6.1,6.3,6.2,6.4],
        "Tomás Jesús Villagrán Soto": [6.4,6.3,6.2,6.4,6.5,6.3,6.4,6.2,6.3,6.4],
        "Humberto Segundo Zúñiga Muñoz": [5.9,6.0,5.8,6.1,6.0,5.9,6.1,6.0,6.2,6.1],
        "Doris Magaly Álvarez Rondón": [6.3,6.4,6.2,6.5,6.3,6.4,6.5,6.4,6.3,6.2],
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
                    "profesor": asignatura.profesor,  #  profesor obligatorio
                    "evaluacion": f"Nota {i}"
                }
            )
            creadas += 1

    print(f" {creadas} notas creadas o actualizadas correctamente para {encontradas} alumnos.")
