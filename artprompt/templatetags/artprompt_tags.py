from django import template

register = template.Library()


@register.filter
def shout(value):
    return str(value).upper()


@register.simple_tag
def site_message():
    return "Добро пожаловать в ArtPrompt!"