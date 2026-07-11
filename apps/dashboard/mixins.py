"""Reusable mixins for dashboard views."""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

logger = logging.getLogger("dashboard")


class StaffRequiredMixin(LoginRequiredMixin):
    """Allow only staff (is_staff=True) users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin(LoginRequiredMixin):
    """Allow only superusers."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class ManagerRequiredMixin(StaffRequiredMixin):
    """Allow superusers and users in the 'Manager' group."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_superuser:
            return response
        if not request.user.groups.filter(name="Manager").exists():
            raise Http404
        return response


class AuditMixin:
    """Log CRUD actions to the dashboard audit logger."""

    def log_action(self, action: str, model: str, pk=None):
        logger.info(
            "[DASHBOARD] %s %s %s%s",
            self.request.user,
            action,
            model,
            f" id={pk}" if pk else "",
        )
