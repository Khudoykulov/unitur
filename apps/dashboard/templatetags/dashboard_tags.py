"""Template tags for the dashboard."""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def user_role(user):
    """Return the user's current role as a string."""
    if user.is_superuser:
        return "superuser"
    if user.is_staff:
        if user.groups.filter(name="Manager").exists():
            return "manager"
        if user.groups.filter(name="Operator").exists():
            return "operator"
        return "staff"
    return "user"


@register.simple_tag
def active_link(request, url_name):
    """Return 'active' CSS class if current URL matches."""
    from django.urls import reverse, NoReverseMatch
    try:
        target = reverse(url_name)
        if request.path.startswith(target):
            return "active"
    except NoReverseMatch:
        pass
    return ""


@register.filter
def status_badge(value):
    """Render a coloured badge for booking/review status."""
    colours = {
        "draft": "bg-gray-100 text-gray-600",
        "submitted": "bg-yellow-100 text-yellow-700",
        "confirmed": "bg-green-100 text-green-700",
        "cancelled": "bg-red-100 text-red-700",
        "completed": "bg-blue-100 text-blue-700",
        "pending": "bg-yellow-100 text-yellow-700",
        "approved": "bg-green-100 text-green-700",
        "rejected": "bg-red-100 text-red-700",
        "open": "bg-green-100 text-green-700",
        "closed": "bg-gray-100 text-gray-600",
        "full": "bg-red-100 text-red-700",
    }
    css = colours.get(value, "bg-gray-100 text-gray-600")
    return mark_safe(f'<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium {css}">{value}</span>')


@register.filter
def star_rating(value):
    """Render filled/empty stars."""
    try:
        n = int(value)
    except (ValueError, TypeError):
        return ""
    filled = "★" * n
    empty = "☆" * (5 - n)
    return mark_safe(
        f'<span class="text-yellow-400">{filled}</span>'
        f'<span class="text-gray-300">{empty}</span>'
    )
