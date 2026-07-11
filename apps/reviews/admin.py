"""Admin configuration for reviews with approve/reject actions."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Review


def approve_reviews(modeladmin, request, queryset):
    queryset.update(status="approved")
approve_reviews.short_description = _("Approve selected reviews")


def reject_reviews(modeladmin, request, queryset):
    queryset.update(status="rejected")
reject_reviews.short_description = _("Reject selected reviews")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "reviewer_name_display", "review_type", "rating_display",
        "title", "status_badge", "is_verified", "created_at"
    )
    list_filter = ("status", "review_type", "rating", "is_verified")
    search_fields = ("title", "body", "guest_name", "user__email")
    readonly_fields = ("created_at", "updated_at", "helpful_count")
    actions = [approve_reviews, reject_reviews]
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("review_type", "status", "is_verified", "tour", "hotel", "user")}),
        (_("Reviewer"), {"fields": ("guest_name", "guest_country")}),
        (_("Content"), {"fields": ("rating", "title", "body", "travel_date")}),
        (_("Stats"), {"fields": ("helpful_count", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def reviewer_name_display(self, obj):
        return obj.reviewer_name
    reviewer_name_display.short_description = _("Reviewer")

    def rating_display(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)
    rating_display.short_description = _("Rating")

    def status_badge(self, obj):
        colors = {"pending": "#f59e0b", "approved": "#16a34a", "rejected": "#dc2626"}
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = _("Status")
