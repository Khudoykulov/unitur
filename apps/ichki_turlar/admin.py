"""Admin for the separate 'Ichki Turlar' section: manage Uzbek cities here.

Cities added here (with cover image, gallery and overview) become the building
blocks selectable when creating a domestic multi-city tour's route.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from apps.destinations.admin import AttractionInline, CityImageInline
from apps.destinations.models import Country

from .models import DomesticCity

# Domestic = Uzbekistan. Matched by name so it survives slug/id changes.
DOMESTIC_COUNTRY = "Uzbek"


@admin.register(DomesticCity)
class DomesticCityAdmin(TranslationAdmin):
    list_display = ("name", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CityImageInline, AttractionInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "cover_image", "is_featured", "is_active", "order")}),
        (_("Information"), {"fields": ("overview", "population", "latitude", "longitude")}),
        (_("SEO"), {"fields": ("seo_title", "seo_description"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        # Match the language-independent English name (name_en); ``country__name``
        # resolves to the active admin language under modeltranslation.
        return super().get_queryset(request).filter(
            country__name_en__icontains=DOMESTIC_COUNTRY
        )

    def save_model(self, request, obj, form, change):
        # New cities added in this section always belong to Uzbekistan.
        if obj.country_id is None:
            obj.country = Country.objects.filter(
                name_en__icontains=DOMESTIC_COUNTRY
            ).first()
        super().save_model(request, obj, form, change)
