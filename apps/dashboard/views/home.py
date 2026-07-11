"""Dashboard home — statistics overview."""

import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.bookings.models import Inquiry
from apps.dashboard.mixins import StaffRequiredMixin
from apps.dashboard.models import DashboardNotification
from apps.reviews.models import Review
from apps.tours.models import Tour
from apps.hotels.models import Hotel


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        ctx.update(
            {
                "total_tours": Tour.objects.count(),
                "total_hotels": Hotel.objects.count(),
                "pending_bookings": Inquiry.objects.filter(status="submitted").count(),
                "pending_reviews": Review.objects.filter(status="pending").count(),
                "monthly_bookings": Inquiry.objects.filter(created_at__gte=month_start).count(),
                "confirmed_bookings": Inquiry.objects.filter(status="confirmed").count(),
                "recent_bookings": (
                    Inquiry.objects.select_related("tour", "hotel")
                    .order_by("-created_at")[:10]
                ),
                "pending_review_list": Review.objects.filter(status="pending").order_by("-created_at")[:5],
                "notifications": DashboardNotification.objects.filter(
                    is_read=False,
                ).filter(
                    recipient=self.request.user
                )[:5],
            }
        )
        return ctx


def dashboard_stats_api(request):
    """AJAX endpoint polled every 60s for live badge counts."""
    if not request.user.is_staff:
        return JsonResponse({}, status=403)
    data = {
        "pending_bookings": Inquiry.objects.filter(status="submitted").count(),
        "pending_reviews": Review.objects.filter(status="pending").count(),
        "notif_count": DashboardNotification.objects.filter(
            is_read=False, recipient=request.user
        ).count(),
    }
    return JsonResponse(data)
