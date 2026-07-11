"""Review list view with filtering by type and rating, plus public submission."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, ListView

from .forms import ReviewCreateForm
from .models import Review


REVIEW_TYPE_CHOICES = [
    ("tour", "Tour Reviews"),
    ("hotel", "Hotel Reviews"),
    ("general", "General Reviews"),
]


class ReviewListView(ListView):
    """Paginated list of approved reviews with optional type/rating filters.

    Also exposes an unbound ``ReviewCreateForm`` so the page can host a
    "Write a Review" panel that POSTs to :class:`ReviewCreateView`.
    """

    model = Review
    template_name = "reviews/list.html"
    context_object_name = "reviews"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Review.objects.filter(status="approved")
            .select_related("user", "tour", "hotel")
            .order_by("-created_at")
        )
        review_type = self.request.GET.get("type")
        if review_type in ("tour", "hotel", "general"):
            qs = qs.filter(review_type=review_type)

        rating = self.request.GET.get("rating")
        if rating and rating.isdigit() and 1 <= int(rating) <= 5:
            qs = qs.filter(rating=int(rating))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_type"] = self.request.GET.get("type", "")
        ctx["current_rating"] = self.request.GET.get("rating", "")
        ctx["review_types"] = REVIEW_TYPE_CHOICES
        ctx.setdefault("form", ReviewCreateForm())
        return ctx


class ReviewCreateView(CreateView):
    """Handle the public "Write a Review" submission.

    New reviews are forced into the ``pending`` state so nothing goes public
    without moderation. On validation errors the reviews page is re-rendered
    with the bound form so the visitor sees exactly what to fix.
    """

    model = Review
    form_class = ReviewCreateForm
    success_url = reverse_lazy("reviews:list")

    def form_valid(self, form):
        review = form.instance
        review.status = "pending"
        if self.request.user.is_authenticated:
            review.user = self.request.user
        # Derive the fields we no longer ask for.
        review.review_type = "tour" if review.tour else "general"
        review.title = Truncator(review.body).chars(60, truncate="…") or _("Review")
        review.travel_date = timezone.localdate()
        messages.success(
            self.request,
            _("Thank you! Your review will appear after moderation."),
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        # Re-render the list page with the bound (error-carrying) form.
        list_view = ReviewListView()
        list_view.request = self.request
        list_view.kwargs = {}
        list_view.object_list = list_view.get_queryset()
        context = list_view.get_context_data(form=form)
        messages.error(
            self.request,
            _("Please correct the errors below and resubmit your review."),
        )
        return self.render_to_response(context)

    def get_template_names(self):
        return ["reviews/list.html"]
