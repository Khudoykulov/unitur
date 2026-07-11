"""
Booking views: multi-step booking form and generic inquiry form.

Rate-limited to 5 submissions per hour per IP.
"""

import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from django_ratelimit.decorators import ratelimit

from apps.tours.models import Tour

from .forms import BookingForm, InquiryForm
from .models import Inquiry
from .tasks import send_booking_confirmation, send_admin_notification

logger = logging.getLogger(__name__)


def _dispatch_task(task, inquiry_pk: int) -> None:
    """
    Fire a Celery task without ever breaking the request.

    Tries to enqueue asynchronously; if the broker is unavailable
    (Redis down / no worker), falls back to running it synchronously.
    Any failure is logged but never raised to the user.
    """
    try:
        task.delay(inquiry_pk)
    except Exception:
        logger.warning("Broker unavailable for %s; running synchronously", task.name)
        try:
            task(inquiry_pk)
        except Exception:
            logger.exception("Notification %s failed for inquiry %s", task.name, inquiry_pk)


@method_decorator(ratelimit(key="ip", rate="5/h", method="POST", block=True), name="dispatch")
class BookingFormView(FormView):
    """
    Tour booking form.

    Collects contact details for a chosen tour.
    Rate-limited: 5 submissions per hour per IP.
    """

    template_name = "tours/booking.html"
    form_class = BookingForm

    def get_initial(self):
        initial = super().get_initial()
        tour_slug = self.kwargs.get("slug") or self.request.GET.get("tour")
        if tour_slug:
            try:
                tour = Tour.objects.get(slug=tour_slug, is_active=True)
                initial["tour"] = tour.pk
            except Tour.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug")
        if slug:
            ctx["tour"] = get_object_or_404(Tour, slug=slug, is_active=True)
        ctx["steps"] = [
            (1, _("Tour Details")),
            (2, _("Your Info")),
            (3, _("Confirmation")),
        ]
        ctx["current_step"] = 2
        return ctx

    def form_valid(self, form):
        inquiry = form.save(commit=False)
        inquiry.inquiry_type = "tour"
        inquiry.source = "web"
        inquiry.created_ip = self._get_client_ip()
        inquiry.save()

        # Notify admin about the new booking (best-effort, never blocks the user).
        _dispatch_task(send_admin_notification, inquiry.pk)
        # Confirmation to the customer only if they left an email.
        if inquiry.email:
            _dispatch_task(send_booking_confirmation, inquiry.pk)

        return redirect("bookings:confirmation", pk=inquiry.pk)

    def _get_client_ip(self) -> str:
        x_fwd = self.request.META.get("HTTP_X_FORWARDED_FOR")
        return x_fwd.split(",")[0] if x_fwd else self.request.META.get("REMOTE_ADDR", "")


class BookingConfirmationView(TemplateView):
    """Show booking confirmation with reference number."""

    template_name = "bookings/confirmation.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["inquiry"] = get_object_or_404(Inquiry, pk=self.kwargs["pk"])
        return ctx


@method_decorator(ratelimit(key="ip", rate="5/h", method="POST", block=True), name="dispatch")
class InquiryFormView(FormView):
    """Generic inquiry / contact form for custom trip requests."""

    template_name = "bookings/inquiry.html"
    form_class = InquiryForm

    def form_valid(self, form):
        inquiry = form.save(commit=False)
        inquiry.source = "web"
        x_fwd = self.request.META.get("HTTP_X_FORWARDED_FOR")
        inquiry.created_ip = x_fwd.split(",")[0] if x_fwd else self.request.META.get("REMOTE_ADDR", "")
        inquiry.save()
        _dispatch_task(send_admin_notification, inquiry.pk)
        messages.success(self.request, _("Thank you! We'll be in touch within 24 hours."))
        return redirect("bookings:inquiry")
