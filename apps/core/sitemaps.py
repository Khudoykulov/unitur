"""
Sitemap classes for all public-facing pages.

Registered in config/urls.py under /sitemap.xml.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.destinations.models import Country
from apps.guides.models import Article
from apps.hotels.models import Hotel
from apps.tours.models import Tour


class TourSitemap(Sitemap):
    """Sitemap entries for all active tours."""

    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Tour.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CountrySitemap(Sitemap):
    """Sitemap entries for destination country pages."""

    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Country.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class HotelSitemap(Sitemap):
    """Sitemap entries for hotel pages."""

    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Hotel.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class ArticleSitemap(Sitemap):
    """Sitemap entries for published guide articles."""

    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Article.objects.filter(is_published=True, is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages (home, about, contact)."""

    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return ["home", "about", "contact", "tours:list", "destinations:list", "hotels:list"]

    def location(self, item):
        return reverse(item)
