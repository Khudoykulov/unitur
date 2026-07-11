"""Dashboard access middleware — blocks non-staff from /dashboard/."""

from django.core.exceptions import PermissionDenied


class DashboardAccessMiddleware:
    """Deny anyone who isn't an active staff user access to /dashboard/.

    We intentionally raise ``PermissionDenied`` (403) instead of redirecting to
    a login page: there is no public login UI, and redirecting would advertise
    that an auth flow exists. Staff authenticate through the hidden
    Ctrl+Shift+A modal, which logs them in and sends them straight here.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/dashboard/"):
            user = request.user
            if not (user.is_authenticated and user.is_active and user.is_staff):
                raise PermissionDenied
        return self.get_response(request)
