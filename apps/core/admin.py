"""Core admin customizations: custom AdminSite and shared utilities."""

import csv

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import HeroSlide


class TravelProAdminSite(AdminSite):
    """Custom admin site with Travel Pro branding."""

    site_header = "Travel Pro Administration"
    site_title = "Travel Pro Admin"
    index_title = "Dashboard"


# Use the standard admin site — swap to custom if desired
# admin.site = TravelProAdminSite(name="travel_pro_admin")


def export_as_csv(modeladmin, request, queryset):
    """Generic admin action: export selected objects to CSV."""
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={meta.verbose_name_plural}.csv"
    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, f) for f in field_names])
    return response


export_as_csv.short_description = _("Export selected to CSV")


@admin.register(HeroSlide)
class HeroSlideAdmin(TranslationAdmin):
    list_display = ("page", "alt", "is_active", "order", "created_at")
    list_filter = ("page", "is_active")
    list_editable = ("is_active", "order")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("page", "image", "alt", "is_active", "order")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
