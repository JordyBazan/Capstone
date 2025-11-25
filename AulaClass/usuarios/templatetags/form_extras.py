from django import template
register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    attrs = field.field.widget.attrs
    existing = attrs.get('class', '')
    attrs['class'] = (existing + ' ' + css).strip()
    return field.as_widget(attrs=attrs)
