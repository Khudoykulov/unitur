"""Admin configuration for hotel models."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline

from .models import Hotel, HotelAmenity, HotelImage, HotelRoom


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1
    fields = ("image", "caption", "order")


class HotelRoomInline(TranslationStackedInline):
    model = HotelRoom
    extra = 0
    fields = ("room_type", "description", "capacity", "price_per_night", "is_available", "image")


@admin.register(HotelAmenity)
class HotelAmenityAdmin(TranslationAdmin):
    list_display = ("name", "icon", "order")
    list_editable = ("order",)


@admin.register(Hotel)
class HotelAdmin(ImportExportModelAdmin, TranslationAdmin):
    list_display = ("name", "city", "category", "stars", "price_from", "is_featured", "is_active", "order")
    list_filter = ("category", "stars", "city__country", "is_featured", "is_active")
    search_fields = ("name", "city__name")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_featured", "is_active", "order")
    filter_horizontal = ("amenities",)
    inlines = [HotelImageInline, HotelRoomInline]

    fieldsets = (
        (None, {"fields": ("name", "slug", "city", "category", "stars", "cover_image", "is_featured", "is_active", "order")}),
        (_("Contact"), {"fields": ("address", "phone", "email", "website", "latitude", "longitude")}),
        (_("Info"), {"fields": ("description", "amenities", "check_in_time", "check_out_time", "price_from")}),
        (_("SEO"), {"fields": ("seo_title", "seo_description"), "classes": ("collapse",)}),
    )
