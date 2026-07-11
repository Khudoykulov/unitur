"""Context processor that injects badge counts into every dashboard page."""

from apps.bookings.models import Inquiry
from apps.reviews.models import Review


def dashboard_counts(request):
    if not request.path.startswith("/dashboard/") or not getattr(request.user, "is_staff", False):
        return {}
    return {
        "pending_booking_count": Inquiry.objects.filter(status="submitted").count(),
        "pending_review_count": Review.objects.filter(status="pending").count(),
    }
