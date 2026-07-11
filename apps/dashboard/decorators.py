"""Function-based view decorators for dashboard access control."""

from functools import wraps

from django.http import Http404
from django.shortcuts import redirect


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if not request.user.is_staff:
            raise Http404
        return view_func(request, *args, **kwargs)
    return _wrapped


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if not request.user.is_superuser:
            raise Http404
        return view_func(request, *args, **kwargs)
    return _wrapped
