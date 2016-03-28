from django import template


register = template.Library()


@register.filter(takes_context=True)
def media_clean(media, **kwargs):
    return media