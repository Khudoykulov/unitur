from django import template

register = template.Library()


@register.filter
def getitem(obj, key):
    """Dictionary/object attribute lookup by variable key."""
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return None
