"""Presentation helpers only; answer keys remain unchanged in the database."""
from django import template
register = template.Library()

@register.filter
def option_label(option):
    key = (option.option_key or "").strip()
    text = (option.option_text or "").strip()
    if not text:
        return key
    # True/True, False/False, Not Given/Not Given must not duplicate visibly.
    if key.casefold().rstrip(".: ") == text.casefold().rstrip(".: "):
        return text
    return f"{key}. {text}" if key else text
