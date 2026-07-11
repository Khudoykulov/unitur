"""Admin configuration for dashboard models."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import AdminLoginLog, DashboardNotification


@admin.register(AdminLoginLog)
class AdminLoginLogAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "ip_address", "success", "created_at")
    list_filter = ("success", "created_at")
    search_fields = ("email", "ip_address", "user__username")
    readonly_fields = ("user", "email", "ip_address", "user_agent", "success", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DashboardNotification)
class DashboardNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "level", "is_read", "created_at")
    list_filter = ("level", "is_read", "created_at")
    search_fields = ("title", "message", "recipient__username", "recipient__email")
    readonly_fields = ("created_at",)
    list_editable = ("is_read",)
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("recipient", "level", "title", "message", "link")}),
        (_("Status"), {"fields": ("is_read", "created_at")}),
    )
