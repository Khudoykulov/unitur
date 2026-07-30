"""Dashboard CRUD views for Hotels."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.forms import HotelForm
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.hotels.models import Hotel, HotelAmenity, HotelImage


class HotelListView(ManagerRequiredMixin, ListView):
    model = Hotel
    template_name = "dashboard/hotels/list.html"
    context_object_name = "hotels"
    paginate_by = 20

    def get_queryset(self):
        qs = Hotel.objects.select_related("city__country").order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class HotelCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = Hotel
    form_class = HotelForm
    template_name = "dashboard/hotels/form.html"
    success_url = reverse_lazy("dashboard:hotels_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)

        # Handle multiple uploaded gallery images
        gallery_files = self.request.FILES.getlist("gallery_images")
        for f in gallery_files:
            HotelImage.objects.create(hotel=self.object, image=f)

        self.log_action("CREATE", "Hotel", self.object.pk)
        messages.success(self.request, gettext("Hotel '%(name)s' created.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Create Hotel")
        ctx["all_amenities"] = HotelAmenity.objects.all().order_by("name")
        return ctx


class HotelEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = Hotel
    form_class = HotelForm
    template_name = "dashboard/hotels/form.html"
    success_url = reverse_lazy("dashboard:hotels_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)

        # Delete selected gallery images
        delete_ids = self.request.POST.getlist("delete_image_ids")
        if delete_ids:
            HotelImage.objects.filter(hotel=self.object, pk__in=delete_ids).delete()

        # Handle multiple uploaded gallery images
        gallery_files = self.request.FILES.getlist("gallery_images")
        for f in gallery_files:
            HotelImage.objects.create(hotel=self.object, image=f)

        self.log_action("UPDATE", "Hotel", self.object.pk)
        messages.success(self.request, gettext("Hotel '%(name)s' updated.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {"name": self.object.name}
        ctx["all_amenities"] = HotelAmenity.objects.all().order_by("name")
        if self.object:
            ctx["selected_amenity_ids"] = set(self.object.amenities.values_list("id", flat=True))
            ctx["gallery_images"] = self.object.gallery.all()
        return ctx


class HotelDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = Hotel
    success_url = reverse_lazy("dashboard:hotels_list")
    # GET shows the confirmation page; POST (list button or that page) deletes.
    template_name = "dashboard/confirm_delete.html"

    def form_valid(self, form):
        self.log_action("DELETE", "Hotel", self.object.pk)
        messages.success(self.request, gettext("Hotel '%(name)s' deleted.") % {"name": self.object.name})
        return super().form_valid(form)
