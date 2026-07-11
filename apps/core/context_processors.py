"""
Global context processors injected into every template.

Provides site settings, navigation data, and language list.
"""

from django.conf import settings

from apps.destinations.models import Continent
from apps.tours.models import TourCategory


def site_settings(request) -> dict:
    """Inject site-wide configuration from settings."""
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "Travel Pro"),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE", "Discover the World"),
        "SITE_PHONE": getattr(settings, "SITE_PHONE", ""),
        "SITE_EMAIL": getattr(settings, "SITE_EMAIL", ""),
        "SITE_ADDRESS": getattr(settings, "SITE_ADDRESS", ""),
        "SITE_LATITUDE": getattr(settings, "SITE_LATITUDE", None),
        "SITE_LONGITUDE": getattr(settings, "SITE_LONGITUDE", None),
        "SITE_WORKING_HOURS": getattr(settings, "SITE_WORKING_HOURS", ""),
        "SOCIAL_LINKS": getattr(settings, "SOCIAL_LINKS", {}),
    }


def navigation(request) -> dict:
    """Inject tour categories and continents for mega-menu rendering."""
    return {
        "nav_tour_categories": TourCategory.objects.all().order_by("order"),
        "nav_continents": Continent.objects.prefetch_related(
            "countries"
        ).order_by("order"),
    }


def languages(request) -> dict:
    """Inject language list with flag emoji for the language switcher."""
    language_flags = getattr(settings, "LANGUAGE_FLAGS", {})
    current_language = getattr(request, "LANGUAGE_CODE", settings.LANGUAGE_CODE)
    return {
        "LANGUAGES": settings.LANGUAGES,
        "LANGUAGE_FLAGS": language_flags,
        "CURRENT_LANGUAGE": current_language,
    }
