from django import template

from fees.utils import format_ugx


register = template.Library()


@register.filter
def ugx(value):
    return format_ugx(value)
