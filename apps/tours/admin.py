"""Admin configuration for tour models with inline editing."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline, TranslationTabularInline

from apps.core.admin import export_as_csv

from .models import Tour, TourCategory, TourDay, TourDeparture, TourImage, TourStop


class TourStopInline(admin.TabularInline):
    model = TourStop
    extra = 1
    fields = ("order", "city", "nights")
    ordering = ("order",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Domestic ("Ichki Turlar") routes are built only from Uzbek cities.
        if db_field.name == "city":
            from apps.destinations.models import City

            kwargs["queryset"] = City.objects.filter(
                country__name_en__icontains="Uzbek", is_active=True
            ).order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TourDayInline(TranslationStackedInline):
    model = TourDay
    extra = 1
    fields = ("day_number", "title", "description", "meals_included", "accommodation", "transport", "image")
    ordering = ("day_number",)


class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 1
    fields = ("image", "caption", "order")
    ordering = ("order",)


class TourDepartureInline(admin.TabularInline):
    model = TourDeparture
    extra = 1
    fields = ("departure_date", "return_date", "available_seats", "booked_seats", "price_override", "status")
    readonly_fields = ("booked_seats",)


@admin.register(TourCategory)
class TourCategoryAdmin(TranslationAdmin):
    list_display = ("name", "slug", "icon", "order")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("order",)


@admin.register(Tour)
class TourAdmin(ImportExportModelAdmin, TranslationAdmin):
    list_display = (
        "title",
        "category",
        "duration_days",
        "difficulty",
        "price_display",
        "is_featured",
        "is_active",
        "views_count",
        "order",
    )
    list_filter = ("category", "difficulty", "is_featured", "is_active", "destinations")
    search_fields = ("title", "overview")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_featured", "is_active", "order")
    filter_horizontal = ("destinations", "hotels")
    readonly_fields = ("views_count", "created_at", "updated_at")
    actions = [export_as_csv]
    inlines = [TourStopInline, TourDayInline, TourImageInline, TourDepartureInline]

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "category", "cover_image", "is_featured", "is_active", "order"),
        }),
        (_("Details"), {
            "fields": ("duration_days", "difficulty", "group_size_min", "group_size_max", "destinations", "hotels"),
        }),
        (_("Pricing"), {
            "fields": ("price_per_person", "price_currency", "discount_percent"),
        }),
        (_("Content"), {
            "fields": ("overview", "includes", "excludes", "important_notes"),
        }),
        (_("SEO"), {
            "fields": ("seo_title", "seo_description"),
            "classes": ("collapse",),
        }),
        (_("Stats"), {
            "fields": ("views_count", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def price_display(self, obj):
        if obj.discount_percent:
            return format_html(
                '<span style="text-decoration:line-through">{}</span> <strong>{}</strong> {}',
                f"{obj.price_per_person} {obj.price_currency}",
                f"{obj.discounted_price:.2f}",
                obj.price_currency,
            )
        return f"{obj.price_per_person} {obj.price_currency}"
    price_display.short_description = _("Price")


@admin.register(TourDeparture)
class TourDepartureAdmin(admin.ModelAdmin):
    list_display = ("tour", "departure_date", "return_date", "available_seats", "booked_seats", "seats_left_display", "status")
    list_filter = ("status", "tour__category")
    search_fields = ("tour__title",)
    date_hierarchy = "departure_date"
    list_editable = ("status",)

    def seats_left_display(self, obj):
        color = "green" if obj.seats_left > 5 else ("orange" if obj.seats_left > 0 else "red")
        return format_html('<span style="color:{}">{}</span>', color, obj.seats_left)
    seats_left_display.short_description = _("Seats left")
