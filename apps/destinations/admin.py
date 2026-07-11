"""Admin configuration for destination models."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline

from .models import Attraction, City, CityImage, Continent, Country


class CityImageInline(TranslationStackedInline):
    """Gallery images for a city. Stacked so each image's translated caption
    and description are editable per language. Unlimited rows (extra=3)."""

    model = CityImage
    extra = 3
    fields = ("image", "caption", "description", "order")
    ordering = ("order",)
    verbose_name = _("Gallery image")
    verbose_name_plural = _("Gallery images")


class CityInline(admin.TabularInline):
    model = City
    extra = 0
    fields = ("name", "slug", "is_featured", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}
    show_change_link = True


class AttractionInline(admin.TabularInline):
    model = Attraction
    extra = 0
    fields = ("name", "category", "is_featured", "is_active")
    show_change_link = True


@admin.register(Continent)
class ContinentAdmin(TranslationAdmin):
    list_display = ("name", "slug", "country_count", "order")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order",)

    def country_count(self, obj):
        return obj.countries.count()
    country_count.short_description = _("Countries")


@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin, TranslationAdmin):
    list_display = (
        "name", "continent", "is_featured", "is_active", "tour_count_display", "order"
    )
    list_filter = ("continent", "is_featured", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_featured", "is_active", "order")
    inlines = [CityInline]
    fieldsets = (
        (None, {"fields": ("continent", "name", "slug", "flag_image", "cover_image", "is_featured", "is_active", "order")}),
        (_("Travel Info"), {"fields": ("overview", "visa_info", "best_time_to_visit", "currency", "language", "timezone")}),
        (_("SEO"), {"fields": ("seo_title", "seo_description"), "classes": ("collapse",)}),
    )

    def tour_count_display(self, obj):
        return obj.tour_count
    tour_count_display.short_description = _("Tours")


@admin.register(City)
class CityAdmin(TranslationAdmin):
    list_display = ("name", "country", "is_featured", "is_active", "order")
    list_filter = ("country", "is_featured", "is_active")
    search_fields = ("name", "country__name")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_featured", "is_active", "order")
    # Field order: cover image first, then the overview text; the gallery images
    # (optional, unlimited) are added below via the inline.
    fieldsets = (
        (None, {"fields": ("country", "name", "slug", "cover_image", "overview")}),
        (_("Details"), {"fields": ("population", "latitude", "longitude", "is_featured", "is_active", "order")}),
        (_("SEO"), {"fields": ("seo_title", "seo_description"), "classes": ("collapse",)}),
    )
    inlines = [CityImageInline, AttractionInline]


@admin.register(Attraction)
class AttractionAdmin(TranslationAdmin):
    list_display = ("name", "city", "category", "is_featured", "is_active")
    list_filter = ("category", "city__country", "is_featured")
    search_fields = ("name", "city__name")
    prepopulated_fields = {"slug": ("name",)}
