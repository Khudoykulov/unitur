"""
URL configuration for UNITUR travel agency project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from django.views.i18n import JavaScriptCatalog

from apps.core.sitemaps import (
    ArticleSitemap,
    CountrySitemap,
    HotelSitemap,
    StaticViewSitemap,
    TourSitemap,
)
from apps.core.views import RobotsTxtView
from apps.destinations.views import CityInfoAPIView
from apps.tours.views import IchkiTurlarListView

sitemaps = {
    "tours": TourSitemap,
    "destinations": CountrySitemap,
    "hotels": HotelSitemap,
    "articles": ArticleSitemap,
    "static": StaticViewSitemap,
}

urlpatterns = [
    # Admin (hidden URL)
    path(getattr(settings, "ADMIN_URL", "admin/"), admin.site.urls),
    # Dashboard
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    # i18n
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    # Rosetta translations (dev)
    path("rosetta/", include("rosetta.urls")),
    # CKEditor
    path("ckeditor/", include("ckeditor_uploader.urls")),
    # django-allauth
    path("accounts/", include("allauth.urls")),
    # SEO
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", RobotsTxtView.as_view(), name="robots-txt"),
    # App URLs
    path("", include("apps.core.urls")),
    path("tours/", include("apps.tours.urls", namespace="tours")),
    path("destinations/", include("apps.destinations.urls", namespace="destinations")),
    path("hotels/", include("apps.hotels.urls", namespace="hotels")),
    path("guides/", include("apps.guides.urls", namespace="guides")),
    path("reviews/", include("apps.reviews.urls", namespace="reviews")),
    path("bookings/", include("apps.bookings.urls", namespace="bookings")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    # Ichki Turlar (multi-city tours) — reuses the Tours app
    path("ichki-turlar/", IchkiTurlarListView.as_view(), name="ichki-turlar-list"),
    # JSON API for the interactive route line on multi-city tours
    path("api/cities/<slug:slug>/info/", CityInfoAPIView.as_view(), name="city-info-api"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

