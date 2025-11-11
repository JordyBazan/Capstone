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
    asignatura = Asignatura.objects.filter(nombre__icontains="Educación Física", curso=curso).first()

    if not curso or not asignatura:
        print(" No se encontró el curso o la asignatura.")
        return

    print(f" Cargando notas para {asignatura.nombre} - {curso.nombre}")

    # === Notas ficticias ===
    notas_data = {
        "Daniel Alexis Bustos Cárcamo": [6.5,6.7,6.8,6.6,6.4,6.5,6.6,6.7,6.8,6.5],
        "Ariel Patricio Báez Sepulveda": [5.9,6.0,6.1,6.2,6.0,6.3,6.2,6.1,6.3,6.2],
        "Erik Fernando Caiza Jimenez": [6.8,6.7,6.5,6.6,6.8,6.7,6.6,6.8,6.7,6.6],
        "Martina Cardonne Arris": [6.4,6.3,6.2,6.5,6.4,6.3,6.5,6.6,6.4,6.3],
        "Juan Carlos Carreño Ortega": [5.8,6.0,5.9,6.1,6.0,5.9,6.1,6.2,6.0,6.1],
        "Verónica Jacqueline Casas Piñeda": [6.7,6.6,6.8,6.7,6.5,6.6,6.7,6.8,6.7,6.6],
        "Gonzalo Alfonso Colman Garrido": [5.9,6.0,6.2,6.1,6.3,6.2,6.0,6.1,6.2,6.0],
        "Paola Andrea Correa Cifuentes": [6.4,6.5,6.3,6.4,6.6,6.4,6.5,6.3,6.6,6.4],
        "Pedro Alexis Covarrubias González": [6.0,6.1,6.3,6.2,6.4,6.2,6.1,6.3,6.2,6.1],
        "Cecilia Andrea Díaz Carrasco": [6.8,6.7,6.6,6.8,6.7,6.8,6.6,6.7,6.8,6.7],
        "Adriana Ignacia Escobar Muñoz": [6.1,6.0,6.2,6.1,6.3,6.2,6.1,6.3,6.2,6.0],
        "Dominic Valentina Espina Díaz": [6.7,6.8,6.6,6.7,6.8,6.7,6.8,6.6,6.7,6.8],
        "Paulo Andrés Espinoza Cortés": [6.2,6.3,6.1,6.4,6.2,6.3,6.4,6.2,6.3,6.1],
        "Johan Antonio Farías Lecaros": [5.9,6.0,6.1,6.2,6.0,6.3,6.2,6.1,6.3,6.2],
        "Matilde Mariela Ibáñez González": [6.6,6.7,6.8,6.6,6.4,6.5,6.6,6.7,6.8,6.5],
        "Gabriel Marcos Llanquileo Saldaña": [6.3,6.2,6.4,6.3,6.5,6.3,6.2,6.4,6.3,6.5],
        "Camila Andrea Lovera Leufuman": [6.5,6.4,6.3,6.6,6.5,6.4,6.3,6.6,6.4,6.5],
        "Roció Tabita Matamala Flores": [6.0,6.1,6.2,6.0,6.3,6.1,6.0,6.2,6.3,6.1],
        "Verónica Del Carmen Moya Gutiérrez": [5.9,6.0,6.1,6.2,6.0,6.3,6.2,6.1,6.3,6.2],
        "Genesis Andrea Olavarría Olavarría": [6.8,6.7,6.6,6.8,6.7,6.8,6.6,6.7,6.8,6.7],
        "Carlos Alberto Quezada Valderrama": [6.2,6.3,6.1,6.4,6.2,6.3,6.4,6.2,6.3,6.1],
        "Isidora Andrea Rayen Gómez": [6.5,6.4,6.3,6.6,6.5,6.4,6.3,6.6,6.4,6.5],
        "Ignacio Alejandro Riquelme Torres": [6.0,6.1,6.2,6.0,6.3,6.1,6.0,6.2,6.3,6.1],
        "Oscar Sebastián Rubio Olavarría": [6.4,6.5,6.3,6.4,6.6,6.4,6.5,6.3,6.6,6.4],
        "Matías Alonso Salgado Díaz": [6.7,6.6,6.8,6.7,6.5,6.6,6.7,6.8,6.7,6.6],
        "José Ricardo Sepúlveda González": [5.9,6.0,6.2,6.1,6.3,6.2,6.0,6.1,6.2,6.0],
        "Andrés Eduardo Silva Tobar": [6.6,6.7,6.8,6.6,6.4,6.5,6.6,6.7,6.8,6.5],
        "Tomás Jesús Villagrán Soto": [6.4,6.3,6.2,6.5,6.4,6.3,6.5,6.6,6.4,6.3],
        "Humberto Segundo Zúñiga Muñoz": [6.1,6.0,6.2,6.1,6.3,6.2,6.1,6.3,6.2,6.0],
        "Doris Magaly Álvarez Rondón": [6.8,6.7,6.6,6.8,6.7,6.8,6.6,6.7,6.8,6.7],
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
