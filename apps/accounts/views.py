"""Account views: user profile and the hidden staff-access login endpoint."""

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit

from apps.bookings.models import Inquiry

from .models import AdminLoginLog


def _get_client_ip(request) -> str:
    """Best-effort client IP, honouring the proxy header used elsewhere."""
    x_fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_fwd:
        return x_fwd.split(",")[0].strip()
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR", "")


class UserProfileView(LoginRequiredMixin, TemplateView):
    """
    Authenticated user profile page.

    Shows booking history and saved tours.
    """

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        ctx["inquiries"] = (
            Inquiry.objects.filter(email=user.email)
            .select_related("tour", "hotel")
            .order_by("-created_at")[:20]
        )

        if hasattr(user, "profile"):
            ctx["saved_tours"] = user.profile.saved_tours.filter(is_active=True)[:12]
        else:
            ctx["saved_tours"] = []

        return ctx


@method_decorator(
    ratelimit(key="ip", rate="5/10m", method="POST", block=True), name="post"
)
class StaffLoginView(View):
    """
    POST-only endpoint behind the hidden Ctrl+Shift+A admin-access modal.

    The password is verified server-side via Django's ``authenticate``; it is
    never checked client-side. There is no link to this URL anywhere in the
    public site — the modal form's ``action`` attribute is the only reference.
    """

    def get(self, request, *args, **kwargs):
        # Never reveal a login UI on GET — behave like the page doesn't exist.
        return redirect("home")

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active and user.is_staff:
            login(request, user)
            AdminLoginLog.objects.create(
                user=user, ip_address=_get_client_ip(request) or None
            )
            return redirect("dashboard:home")

        # Wrong credentials or not staff → flag the modal to re-open with an error.
        messages.error(request, "invalid_staff_login")
        referer = request.META.get("HTTP_REFERER")
        if referer:
            return HttpResponseRedirect(referer)
        return redirect("home")
