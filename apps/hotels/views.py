"""Hotel list and detail views."""

from django.views.generic import DetailView, ListView

from .filters import HotelFilter
from .models import Hotel


class HotelListView(ListView):
    """Filterable hotel listing with 12-per-page pagination."""

    model = Hotel
    template_name = "hotels/list.html"
    context_object_name = "hotels"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Hotel.objects.filter(is_active=True)
            .select_related("city__country")
            .prefetch_related("amenities")
        )
        self.filterset = HotelFilter(self.request.GET, queryset=qs)
        return self.filterset.qs.order_by("order", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filterset"] = self.filterset
        return ctx


class HotelDetailView(DetailView):
    """Hotel detail with room types, amenities, and map."""

    model = Hotel
    template_name = "hotels/detail.html"
    context_object_name = "hotel"
    slug_field = "slug"

    def get_queryset(self):
        return (
            Hotel.objects.filter(is_active=True)
            .select_related("city__country")
            .prefetch_related("amenities", "rooms", "gallery", "reviews")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hotel = self.object
        ctx["rooms"] = hotel.rooms.filter(is_available=True)
        ctx["gallery"] = hotel.gallery.all()
        ctx["approved_reviews"] = hotel.reviews.filter(status="approved").order_by("-created_at")[:10]
        return ctx
