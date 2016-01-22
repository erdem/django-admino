from django import template
from django import forms

register = template.Library()


@register.filter(takes_context=True)
def media_clean(media, **kwargs):
    return media