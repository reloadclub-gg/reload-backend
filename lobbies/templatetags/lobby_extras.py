import datetime

from django import template

register = template.Library()


@register.filter(name='format_seconds')
def format_seconds(seconds):
    return str(datetime.timedelta(seconds=seconds))


@register.simple_tag(takes_context=True)
def querystring(context, *args, **kwargs):
    query = context['request'].GET.copy()
    for k in args:
        query.pop(k, None)
    query.update(kwargs)
    return query.urlencode()
