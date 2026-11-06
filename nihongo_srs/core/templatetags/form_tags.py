from django import forms, template

register = template.Library()


@register.filter
def bootstrap(field):
    """Render a bound field with the matching Bootstrap class (and is-invalid on errors)."""
    widget = field.field.widget
    if isinstance(widget, (forms.CheckboxInput,)):
        css = "form-check-input"
    elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
        css = "form-select"
    else:
        css = "form-control"
    if field.errors:
        css += " is-invalid"
    existing = widget.attrs.get("class", "")
    return field.as_widget(attrs={"class": f"{existing} {css}".strip()})
