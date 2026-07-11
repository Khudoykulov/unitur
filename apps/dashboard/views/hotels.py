"""Dashboard CRUD views for Hotels."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.hotels.models import Hotel


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
    template_name = "dashboard/hotels/form.html"
    success_url = reverse_lazy("dashboard:hotels_list")
    fields = [
        "name", "city", "category", "stars", "cover_image",
        "address", "latitude", "longitude", "phone", "email",
        "website", "description", "amenities",
        "check_in_time", "check_out_time", "price_from",
    ]

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("CREATE", "Hotel", self.object.pk)
        messages.success(self.request, gettext("Hotel '%(name)s' created.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Create Hotel")
        return ctx


class HotelEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = Hotel
    template_name = "dashboard/hotels/form.html"
    success_url = reverse_lazy("dashboard:hotels_list")
    fields = [
        "name", "city", "category", "stars", "cover_image",
        "address", "latitude", "longitude", "phone", "email",
        "website", "description", "amenities",
        "check_in_time", "check_out_time", "price_from",
    ]

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("UPDATE", "Hotel", self.object.pk)
        messages.success(self.request, gettext("Hotel '%(name)s' updated.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {"name": self.object.name}
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
