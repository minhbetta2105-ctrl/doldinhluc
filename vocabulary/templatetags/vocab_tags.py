from django import template

register = template.Library()

LEVEL_VI = {"BEGINNER": "Cơ bản", "INTERMEDIATE": "Trung cấp", "ADVANCED": "Nâng cao"}
LEVEL_CLASS = {"BEGINNER": "", "INTERMEDIATE": "blue", "ADVANCED": "gold"}


@register.filter
def level_vi(value):
    return LEVEL_VI.get(value, value)


@register.filter
def level_class(value):
    return LEVEL_CLASS.get(value, "")
