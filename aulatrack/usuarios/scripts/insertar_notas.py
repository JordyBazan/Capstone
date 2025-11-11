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
    asignatura = Asignatura.objects.filter(nombre__icontains="Ciencias Naturales", curso=curso).first()

    if not curso or not asignatura:
        print(" No se encontró el curso o la asignatura.")
        return

    print(f" Cargando notas para {asignatura.nombre} - {curso.nombre}")

    # === Notas ficticias ===
    notas_data = {
        "Daniel Alexis Bustos Cárcamo": [5.8,6.0,5.5,6.2,5.7,5.9,6.1,5.8,6.0,6.3],
        "Ariel Patricio Báez Sepulveda": [5.0,5.3,4.8,5.6,5.5,5.2,5.7,5.9,5.4,5.3],
        "Erik Fernando Caiza Jimenez": [6.2,6.5,6.0,6.1,6.3,6.4,6.0,6.2,6.1,6.3],
        "Martina Cardonne Arris": [5.9,5.8,6.1,5.6,5.9,6.0,6.2,6.1,6.0,6.3],
        "Juan Carlos Carreño Ortega": [5.2,5.5,5.3,5.0,5.4,5.1,5.5,5.2,5.3,5.4],
        "Verónica Jacqueline Casas Piñeda": [6.1,6.0,6.3,6.2,6.4,6.0,6.2,6.1,6.5,6.3],
        "Gonzalo Alfonso Colman Garrido": [4.8,5.0,5.2,4.9,5.1,5.0,5.3,5.4,5.0,5.1],
        "Paola Andrea Correa Cifuentes": [6.0,6.3,6.1,6.4,6.2,6.0,6.5,6.3,6.4,6.1],
        "Pedro Alexis Covarrubias González": [5.5,5.4,5.2,5.7,5.6,5.5,5.3,5.7,5.8,5.5],
        "Cecilia Andrea Díaz Carrasco": [6.4,6.5,6.3,6.2,6.4,6.5,6.6,6.3,6.2,6.4],
    "Adriana Ignacia Escobar Muñoz": [5.3,5.5,5.0,5.2,5.4,5.1,5.3,5.5,5.4,5.2],
        "Dominic Valentina Espina Díaz": [6.1,6.0,6.2,6.3,6.4,6.2,6.1,6.3,6.4,6.2],
        "Paulo Andrés Espinoza Cortés": [5.0,5.2,5.3,5.4,5.1,5.0,5.3,5.2,5.4,5.5],
        "Johan Antonio Farías Lecaros": [4.9,5.0,5.1,5.3,5.2,5.0,5.1,5.3,5.2,5.1],
        "Matilde Mariela Ibáñez González": [6.3,6.2,6.1,6.4,6.3,6.2,6.1,6.3,6.2,6.4],
        "Gabriel Marcos Llanquileo Saldaña": [5.4,5.2,5.3,5.5,5.1,5.4,5.3,5.5,5.4,5.2],
        "Camila Andrea Lovera Leufuman": [6.0,6.1,6.2,6.3,6.1,6.0,6.3,6.2,6.4,6.1],
        "Roció Tabita Matamala Flores": [5.9,5.7,5.6,5.8,5.9,5.8,6.0,5.9,5.8,5.7],
        "Verónica Del Carmen Moya Gutiérrez": [5.1,5.0,5.3,5.2,5.4,5.3,5.2,5.1,5.4,5.3],
        "Genesis Andrea Olavarría Olavarría": [6.5,6.4,6.3,6.2,6.4,6.5,6.6,6.4,6.3,6.5],
        "Carlos Alberto Quezada Valderrama": [4.8,5.0,4.9,5.1,5.0,4.8,5.0,4.9,5.1,5.0],
        "Isidora Andrea Rayen Gómez": [6.2,6.3,6.1,6.2,6.4,6.3,6.1,6.2,6.3,6.2],
        "Ignacio Alejandro Riquelme Torres": [5.5,5.7,5.4,5.6,5.5,5.4,5.6,5.5,5.7,5.6],
        "Oscar Sebastián Rubio Olavarría": [5.2,5.0,5.3,5.1,5.2,5.3,5.0,5.4,5.3,5.1],
        "Matías Alonso Salgado Díaz": [5.8,5.9,6.0,5.7,5.8,5.9,6.0,5.8,5.9,5.7],
        "José Ricardo Sepúlveda González": [5.1,5.2,5.3,5.0,5.4,5.2,5.1,5.3,5.2,5.1],
        "Andrés Eduardo Silva Tobar": [5.9,6.0,5.8,5.7,6.0,5.9,6.1,5.8,6.0,5.9],
        "Tomás Jesús Villagrán Soto": [6.1,6.3,6.2,6.1,6.3,6.2,6.4,6.3,6.2,6.4],
        "Humberto Segundo Zúñiga Muñoz": [4.9,5.0,5.1,5.2,5.3,5.1,5.0,5.2,5.1,5.0],
        "Doris Magaly Álvarez Rondón": [6.3,6.1,6.2,6.4,6.3,6.2,6.5,6.4,6.3,6.2],
    }

    creadas = 0
    encontradas = 0

    for nombre_completo, notas in notas_data.items():
        partes = nombre_completo.split()
        nombres = " ".join(partes[:-2])
        apellidos = " ".join(partes[-2:])

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
                    "profesor": asignatura.profesor,  #  agregado
                    "evaluacion": f"Nota {i}"
                }
            )
            creadas += 1

    print(f" {creadas} notas creadas o actualizadas correctamente para {encontradas} alumnos.")
