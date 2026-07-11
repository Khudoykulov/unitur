"""
Global context processors injected into every template.

Provides site settings, navigation data, and language list.
"""

from django.conf import settings

from apps.destinations.models import Continent
from apps.tours.models import TourCategory
from apps.core.models import SiteSettings


def site_settings(request) -> dict:
    """Inject site-wide configuration from SiteSettings model."""
    # Load settings from database
    site = SiteSettings.load()

    return {
        # Site Information
        "SITE_NAME": site.site_name or getattr(settings, "SITE_NAME", "Travel Pro"),
        "SITE_TAGLINE": site.site_tagline or getattr(settings, "SITE_TAGLINE", "Discover the World"),

        # Contact Information
        "SITE_PHONE": site.phone or getattr(settings, "SITE_PHONE", ""),
        "SITE_PHONE_SECONDARY": site.phone_secondary or "",
        "SITE_EMAIL": site.email or getattr(settings, "SITE_EMAIL", ""),
        "SITE_EMAIL_SECONDARY": site.email_secondary or "",
        "SITE_ADDRESS": site.address or getattr(settings, "SITE_ADDRESS", ""),
        "SITE_WORKING_HOURS": site.working_hours or getattr(settings, "SITE_WORKING_HOURS", ""),

        # Location
        "SITE_LATITUDE": site.latitude or getattr(settings, "SITE_LATITUDE", None),
        "SITE_LONGITUDE": site.longitude or getattr(settings, "SITE_LONGITUDE", None),

        # Social Media Links
        "SOCIAL_LINKS": {
            "facebook": site.facebook_url or "",
            "instagram": site.instagram_url or "",
            "telegram": site.telegram_url or "",
            "youtube": site.youtube_url or "",
            "twitter": site.twitter_url or "",
            "linkedin": site.linkedin_url or "",
        },
        "WHATSAPP_NUMBER": site.whatsapp_number or "",

        # SEO & Analytics
        "GOOGLE_ANALYTICS_ID": site.google_analytics_id or "",
        "FACEBOOK_PIXEL_ID": site.facebook_pixel_id or "",

        # Footer
        "FOOTER_TEXT": site.footer_text or "",
        "COPYRIGHT_TEXT": site.copyright_text or "© 2024 UNITUR. All rights reserved.",

        # Full site settings object for templates
        "site_settings": site,
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
