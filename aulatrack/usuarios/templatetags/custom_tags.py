from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def index(sequence, position):
    """Permite acceder a un índice de una lista dentro del template."""
    try:
        return sequence[position - 1]
    except (IndexError, TypeError):
        return ''