from django import template

register = template.Library()


@register.filter
def getitem(obj, key):
    """Dictionary/object attribute lookup by variable key."""
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return None


@register.filter(name="format_content")
def format_content(value):
    """Format description text preserving paragraph linebreaks and HTML tags (bold, borders, mark, etc.)."""
    if not value:
        return ""
    import re
    from django.utils.safestring import mark_safe
    paragraphs = re.split(r"\n\s*\n", str(value))
    html_paragraphs = []
    for p in paragraphs:
        p_clean = p.strip().replace("\n", "<br>")
        if p_clean:
            html_paragraphs.append(f'<p class="mb-3 last:mb-0">{p_clean}</p>')
    return mark_safe("\n".join(html_paragraphs))
