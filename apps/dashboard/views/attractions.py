"""Dashboard CRUD views for Attractions (Diqqatga sazovor joylar)."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.forms import AttractionForm
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.destinations.models import Attraction, AttractionImage


class AttractionListView(ManagerRequiredMixin, ListView):
    model = Attraction
    template_name = "dashboard/attractions/list.html"
    context_object_name = "attractions"
    paginate_by = 20

    def get_queryset(self):
        qs = Attraction.objects.select_related("city__country").order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class AttractionCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = Attraction
    form_class = AttractionForm
    template_name = "dashboard/attractions/form.html"
    success_url = reverse_lazy("dashboard:attractions_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        lang = getattr(self.request, "LANGUAGE_CODE", None) or get_language()
        autofill_translations(self.object, source_lang=lang, overwrite=False)

        # Handle multiple uploaded gallery images
        gallery_files = self.request.FILES.getlist("gallery_images")
        for f in gallery_files:
            AttractionImage.objects.create(attraction=self.object, image=f)

        self.log_action("CREATE", "Attraction", self.object.pk)
        messages.success(self.request, gettext("Attraction '%(name)s' created.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Add Attraction")
        return ctx


class AttractionEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = Attraction
    form_class = AttractionForm
    template_name = "dashboard/attractions/form.html"
    success_url = reverse_lazy("dashboard:attractions_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        lang = getattr(self.request, "LANGUAGE_CODE", None) or get_language()
        autofill_translations(self.object, source_lang=lang, overwrite=False)

        # Delete selected gallery images
        delete_ids = self.request.POST.getlist("delete_image_ids")
        if delete_ids:
            AttractionImage.objects.filter(attraction=self.object, pk__in=delete_ids).delete()

        # Handle multiple uploaded gallery images
        gallery_files = self.request.FILES.getlist("gallery_images")
        for f in gallery_files:
            AttractionImage.objects.create(attraction=self.object, image=f)

        self.log_action("UPDATE", "Attraction", self.object.pk)
        messages.success(self.request, gettext("Attraction '%(name)s' updated.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {"name": self.object.name}
        if self.object:
            ctx["gallery_images"] = self.object.gallery.all()
        return ctx


class AttractionDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = Attraction
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:attractions_list")

    def form_valid(self, form):
        self.log_action("DELETE", "Attraction", self.object.pk)
        messages.success(self.request, gettext("Attraction '%(name)s' deleted.") % {"name": self.object.name})
        return super().form_valid(form)
