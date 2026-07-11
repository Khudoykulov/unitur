"""Dashboard user management — superuser only."""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import DeleteView, ListView, UpdateView, View
from django.views.generic.edit import FormView

from apps.dashboard.forms import UserCreateForm, UserEditForm
from apps.dashboard.mixins import AuditMixin, SuperuserRequiredMixin
from apps.dashboard.templatetags.dashboard_tags import user_role

User = get_user_model()

VALID_ROLES = {"superuser", "manager", "operator", "user"}


def apply_role(user, role: str) -> bool:
    """Set a user's staff/superuser flags and groups for the given role.

    Returns True if the role was recognised and applied, False otherwise.
    """
    if role == "superuser":
        user.is_staff = True
        user.is_superuser = True
        user.groups.clear()
    elif role == "manager":
        user.is_staff = True
        user.is_superuser = False
        user.groups.set(Group.objects.filter(name="Manager"))
    elif role == "operator":
        user.is_staff = True
        user.is_superuser = False
        user.groups.set(Group.objects.filter(name="Operator"))
    elif role == "user":
        user.is_staff = False
        user.is_superuser = False
        user.groups.clear()
    else:
        return False
    user.save(update_fields=["is_staff", "is_superuser"])
    return True


class UserListView(SuperuserRequiredMixin, ListView):
    model = User
    template_name = "dashboard/users/list.html"
    context_object_name = "users"
    paginate_by = 30

    def get_queryset(self):
        qs = User.objects.prefetch_related("groups").order_by("-date_joined")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(email__icontains=q) | qs.filter(
                first_name__icontains=q
            ) | qs.filter(last_name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["groups"] = Group.objects.all()
        return ctx


class UserCreateView(AuditMixin, SuperuserRequiredMixin, FormView):
    """Create a new account and assign its role — superuser only."""

    form_class = UserCreateForm
    template_name = "dashboard/users/form.html"
    success_url = reverse_lazy("dashboard:users_list")

    def form_valid(self, form):
        user = form.save()
        apply_role(user, form.cleaned_data["role"])
        self.log_action("CREATE", "User", user.pk)
        messages.success(
            self.request,
            gettext("User %(email)s created with role '%(role)s'.")
            % {"email": user.email, "role": form.cleaned_data["role"]},
        )
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Create User")
        return ctx


class UserEditView(AuditMixin, SuperuserRequiredMixin, UpdateView):
    """Edit an existing account's details, role and password — superuser only."""

    model = User
    form_class = UserEditForm
    template_name = "dashboard/users/form.html"
    success_url = reverse_lazy("dashboard:users_list")

    def get_initial(self):
        initial = super().get_initial()
        initial["role"] = user_role(self.object)
        return initial

    def form_valid(self, form):
        user = form.save()

        # Don't let a superuser strip their own access and lock themselves out.
        new_role = form.cleaned_data["role"]
        if user == self.request.user and new_role != "superuser":
            messages.error(self.request, gettext("You cannot change your own role."))
            return redirect("dashboard:users_edit", pk=user.pk)

        apply_role(user, new_role)
        self.log_action("UPDATE", "User", user.pk)
        messages.success(self.request, gettext("User %(email)s updated.") % {"email": user.email})
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {
            "name": self.object.get_full_name() or self.object.email
        }
        ctx["is_edit"] = True
        return ctx


class UserDeleteView(AuditMixin, SuperuserRequiredMixin, DeleteView):
    """Delete an account — superuser only. Self-deletion is blocked."""

    model = User
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:users_list")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object() if request.user.is_authenticated else None
        if self.object and self.object == request.user:
            messages.error(request, gettext("You cannot delete your own account."))
            return redirect("dashboard:users_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = self.object.email
        self.log_action("DELETE", "User", self.object.pk)
        response = super().form_valid(form)
        messages.success(self.request, gettext("User %(email)s deleted.") % {"email": email})
        return response


class UserRoleUpdateView(AuditMixin, SuperuserRequiredMixin, View):
    """Update a user's role (groups + is_staff flag) via POST."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        # Prevent demoting yourself
        if user == request.user:
            messages.error(request, gettext("You cannot change your own role."))
            return redirect("dashboard:users_list")

        role = request.POST.get("role", "")
        if not apply_role(user, role):
            messages.error(request, gettext("Unknown role."))
            return redirect("dashboard:users_list")

        self.log_action("ROLE_CHANGE", "User", pk)
        messages.success(
            request,
            gettext("Role for %(email)s updated to '%(role)s'.")
            % {"email": user.email, "role": role},
        )
        return redirect("dashboard:users_list")
