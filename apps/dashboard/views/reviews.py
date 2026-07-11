"""Dashboard views for review moderation."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext
from django.views.generic import ListView

from apps.dashboard.mixins import AuditMixin, StaffRequiredMixin
from apps.reviews.models import Review


class ReviewListView(AuditMixin, StaffRequiredMixin, ListView):
    model = Review
    template_name = "dashboard/reviews/list.html"
    context_object_name = "reviews"
    paginate_by = 25

    def get_queryset(self):
        qs = Review.objects.select_related("tour", "hotel", "user").order_by("-created_at")
        status = self.request.GET.get("status", "pending")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(guest_name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["selected_status"] = self.request.GET.get("status", "pending")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["pending_count"] = Review.objects.filter(status="pending").count()
        return ctx

    def post(self, request, *args, **kwargs):
        pk = request.POST.get("pk")
        action = request.POST.get("action")
        review = get_object_or_404(Review, pk=pk)
        if action == "approve":
            review.approve()
            self.log_action("APPROVE", "Review", pk)
            messages.success(request, gettext("Review approved."))
        elif action == "reject":
            review.reject()
            self.log_action("REJECT", "Review", pk)
            messages.success(request, gettext("Review rejected."))
        elif action == "delete":
            review.delete()
            self.log_action("DELETE", "Review", pk)
            messages.success(request, gettext("Review deleted."))
        return redirect(request.path + "?" + request.GET.urlencode())
