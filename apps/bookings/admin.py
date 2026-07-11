"""Admin configuration for bookings with bulk actions and CSV export."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin

from apps.core.admin import export_as_csv

from .models import Inquiry

STATUS_COLORS = {
    "draft": "#6b7280",
    "submitted": "#2563eb",
    "confirmed": "#16a34a",
    "cancelled": "#dc2626",
    "completed": "#7c3aed",
}


def action_confirm(modeladmin, request, queryset):
    queryset.update(status="confirmed")
action_confirm.short_description = _("Mark selected as Confirmed")


def action_cancel(modeladmin, request, queryset):
    queryset.update(status="cancelled")
action_cancel.short_description = _("Mark selected as Cancelled")


def action_complete(modeladmin, request, queryset):
    queryset.update(status="completed")
action_complete.short_description = _("Mark selected as Completed")


@admin.register(Inquiry)
class InquiryAdmin(ImportExportModelAdmin):
    list_display = (
        "confirmation_number",
        "full_name_display",
        "phone",
        "email",
        "tour",
        "inquiry_type",
        "status_badge",
        "source",
        "assigned_to",
        "created_at",
    )
    list_display_links = ("confirmation_number", "full_name_display")
    list_filter = ("status", "inquiry_type", "source", "assigned_to", "created_at")
    search_fields = ("first_name", "last_name", "email", "confirmation_number", "phone")
    readonly_fields = ("confirmation_number", "created_ip", "created_at", "updated_at")
    autocomplete_fields = ("tour", "hotel", "departure", "assigned_to")
    list_select_related = ("tour", "hotel", "assigned_to")
    list_per_page = 50
    date_hierarchy = "created_at"
    actions = [action_confirm, action_cancel, action_complete, export_as_csv]

    fieldsets = (
        (_("Booking Reference"), {
            "fields": ("confirmation_number", "inquiry_type", "status", "source", "assigned_to"),
        }),
        (_("Linked Items"), {
            "fields": ("tour", "departure", "hotel"),
        }),
        (_("Customer"), {
            "fields": ("first_name", "last_name", "email", "phone", "country_of_origin"),
        }),
        (_("Travel Details"), {
            "fields": ("travel_date", "num_adults", "num_children", "budget_range", "special_requests"),
        }),
        (_("Internal"), {
            "fields": ("notes", "created_ip", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def full_name_display(self, obj):
        return obj.full_name
    full_name_display.short_description = _("Customer")

    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = _("Status")
    status_badge.allow_tags = True
