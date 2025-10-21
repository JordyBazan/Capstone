from django import template
register = template.Library()

@register.filter
def index(lista, i):
    """Devuelve el elemento i-ésimo de una lista o queryset"""
    try:
        return lista[i]
    except (IndexError, TypeError):
        return ''
