"""Dashboard views for Bookings / Inquiries."""

import csv
import logging

from django.contrib import messages
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext
from django.views.generic import DetailView, ListView

from apps.bookings.models import Inquiry
from apps.dashboard.mixins import AuditMixin, StaffRequiredMixin

logger = logging.getLogger("dashboard")


class BookingListView(StaffRequiredMixin, ListView):
    model = Inquiry
    template_name = "dashboard/bookings/list.html"
    context_object_name = "bookings"
    paginate_by = 25

    def get_queryset(self):
        qs = Inquiry.objects.select_related("tour", "category", "hotel", "assigned_to").order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(first_name__icontains=q) | qs.filter(
                last_name__icontains=q
            ) | qs.filter(email__icontains=q) | qs.filter(confirmation_number__icontains=q)
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status=status)
        itype = self.request.GET.get("type", "")
        if itype:
            qs = qs.filter(inquiry_type=itype)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["selected_type"] = self.request.GET.get("type", "")
        ctx["status_choices"] = Inquiry.STATUS_CHOICES
        ctx["type_choices"] = Inquiry.INQUIRY_TYPE_CHOICES
        return ctx


class BookingDetailView(AuditMixin, StaffRequiredMixin, DetailView):
    model = Inquiry
    template_name = "dashboard/bookings/detail.html"
    context_object_name = "booking"

    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        action = request.POST.get("action", "")
        if action == "status":
            new_status = request.POST.get("status", "")
            if new_status in dict(Inquiry.STATUS_CHOICES):
                booking.status = new_status
                booking.save(update_fields=["status"])
                self.log_action("STATUS_CHANGE", "Inquiry", booking.pk)
                messages.success(request, gettext("Status updated to %(status)s.") % {"status": booking.get_status_display()})
        elif action == "notes":
            booking.notes = request.POST.get("notes", "")
            booking.save(update_fields=["notes"])
            self.log_action("NOTES_UPDATE", "Inquiry", booking.pk)
            messages.success(request, gettext("Internal notes saved."))
        return redirect("dashboard:booking_detail", pk=booking.pk)


def booking_export_csv(request):
    """Stream all bookings as CSV."""
    if not request.user.is_staff:
        from django.http import Http404
        raise Http404

    def rows():
        header = [
            "Confirmation", "Type", "Status", "First Name", "Last Name",
            "Email", "Phone", "Travel Date", "Adults", "Children",
            "Tour", "Hotel", "Budget", "Source", "Created",
        ]
        yield ",".join(header) + "\n"
        for b in Inquiry.objects.select_related("tour", "hotel").iterator(chunk_size=200):
            row = [
                b.confirmation_number,
                b.inquiry_type,
                b.status,
                b.first_name,
                b.last_name,
                b.email,
                b.phone,
                str(b.travel_date or ""),
                str(b.num_adults),
                str(b.num_children),
                str(b.tour or ""),
                str(b.hotel or ""),
                b.budget_range,
                b.source,
                b.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
            yield ",".join(f'"{c}"' for c in row) + "\n"

    response = StreamingHttpResponse(rows(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="bookings.csv"'
    logger.info("[DASHBOARD] %s exported bookings CSV", request.user)
    return response
