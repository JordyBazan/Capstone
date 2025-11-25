from django import template

register = template.Library()

@register.filter
def index(sequence, position):
    """
    Devuelve el elemento en la posición dada (1-indexado).
    Uso: {{ mi_lista|index:2 }} → devuelve el segundo elemento.
    """
    try:
        pos = int(position) - 1
        return sequence[pos]
    except Exception:
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
