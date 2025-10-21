from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def index(sequence, position):
    """
    Devuelve el elemento en la posición indicada de una lista o tupla.
    Uso: {{ mi_lista|index:0 }}
    """
    try:
        position = int(position)
        return sequence[position]
    except (IndexError, ValueError, TypeError):
        return ''

@register.filter
def get_item(dictionary, key):
    """
    Devuelve un valor de un diccionario con la clave dada.
    Uso: {{ mi_dict|get_item:"clave" }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''
