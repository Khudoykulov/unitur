"""Tests for dashboard user creation and role assignment (superuser-only)."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.dashboard.forms import UserCreateForm, UserEditForm
from apps.dashboard.views.users import apply_role
from tests import factories as f

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def groups():
    Group.objects.get_or_create(name="Manager")
    Group.objects.get_or_create(name="Operator")


@pytest.fixture
def super_client(client):
    user = f.make_user(username="root", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    return client


class TestUserCreateForm:
    def test_valid(self):
        form = UserCreateForm(
            data={
                "email": "new@example.com",
                "password": "Str0ngPass!",
                "role": "manager",
            }
        )
        assert form.is_valid(), form.errors

    def test_email_normalized_lowercase(self):
        form = UserCreateForm(
            data={"email": "MixedCase@Example.com", "password": "Str0ngPass!", "role": "user"}
        )
        assert form.is_valid()
        assert form.cleaned_data["email"] == "mixedcase@example.com"

    def test_duplicate_email_rejected(self):
        f.make_user(email="dupe@example.com")
        form = UserCreateForm(
            data={"email": "dupe@example.com", "password": "Str0ngPass!", "role": "user"}
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_short_password_rejected(self):
        form = UserCreateForm(
            data={"email": "x@example.com", "password": "123", "role": "user"}
        )
        assert not form.is_valid()
        assert "password" in form.errors

    def test_save_sets_username_to_email_and_hashes_password(self):
        form = UserCreateForm(
            data={"email": "a@b.com", "password": "Str0ngPass!", "role": "user"}
        )
        assert form.is_valid(), form.errors
        user = form.save()
        assert user.username == "a@b.com"
        assert user.email == "a@b.com"
        assert user.password != "Str0ngPass!"
        assert user.check_password("Str0ngPass!")


class TestApplyRole:
    def test_superuser(self):
        u = f.make_user()
        assert apply_role(u, "superuser") is True
        u.refresh_from_db()
        assert u.is_superuser and u.is_staff

    def test_manager_sets_group(self, groups):
        u = f.make_user()
        apply_role(u, "manager")
        u.refresh_from_db()
        assert u.is_staff and not u.is_superuser
        assert u.groups.filter(name="Manager").exists()

    def test_operator_sets_group(self, groups):
        u = f.make_user()
        apply_role(u, "operator")
        u.refresh_from_db()
        assert u.groups.filter(name="Operator").exists()

    def test_user_clears_staff(self):
        u = f.make_user(is_staff=True)
        apply_role(u, "user")
        u.refresh_from_db()
        assert not u.is_staff and not u.is_superuser

    def test_unknown_role_returns_false(self):
        u = f.make_user()
        assert apply_role(u, "wizard") is False


class TestUserCreateView:
    def test_get_form_as_superuser(self, super_client):
        resp = super_client.get(reverse("dashboard:users_create"))
        assert resp.status_code == 200

    def test_create_manager(self, super_client, groups):
        resp = super_client.post(
            reverse("dashboard:users_create"),
            {"email": "mgr@example.com", "password": "Str0ngPass!", "role": "manager"},
        )
        assert resp.status_code == 302
        user = User.objects.get(email="mgr@example.com")
        assert user.is_staff and not user.is_superuser
        assert user.groups.filter(name="Manager").exists()
        assert user.check_password("Str0ngPass!")

    def test_create_superuser_role(self, super_client):
        super_client.post(
            reverse("dashboard:users_create"),
            {"email": "boss@example.com", "password": "Str0ngPass!", "role": "superuser"},
        )
        user = User.objects.get(email="boss@example.com")
        assert user.is_superuser

    def test_create_plain_user(self, super_client):
        super_client.post(
            reverse("dashboard:users_create"),
            {"email": "joe@example.com", "password": "Str0ngPass!", "role": "user"},
        )
        user = User.objects.get(email="joe@example.com")
        assert not user.is_staff

    def test_duplicate_email_shows_error_no_create(self, super_client):
        f.make_user(email="taken@example.com")
        before = User.objects.count()
        resp = super_client.post(
            reverse("dashboard:users_create"),
            {"email": "taken@example.com", "password": "Str0ngPass!", "role": "user"},
        )
        assert resp.status_code == 200  # re-rendered with errors
        assert User.objects.count() == before

    def test_requires_superuser_manager_forbidden(self, client, groups):
        manager = f.make_user(username="m", password="x", is_staff=True)
        manager.groups.add(Group.objects.get(name="Manager"))
        client.force_login(manager)
        resp = client.get(reverse("dashboard:users_create"))
        assert resp.status_code in (302, 403, 404)
        assert resp.status_code != 200

    def test_requires_login(self, client):
        resp = client.get(reverse("dashboard:users_create"))
        assert resp.status_code in (302, 403, 404)


class TestUserEditForm:
    def test_edit_details_without_password_change(self):
        user = f.make_user(email="old@example.com")
        original_hash = user.password
        form = UserEditForm(
            data={
                "email": "old@example.com",
                "first_name": "New",
                "last_name": "Name",
                "is_active": True,
                "role": "user",
                "password": "",
            },
            instance=user,
        )
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.first_name == "New"
        assert saved.password == original_hash  # unchanged

    def test_edit_changes_password_when_provided(self):
        user = f.make_user(email="p@example.com")
        form = UserEditForm(
            data={
                "email": "p@example.com",
                "is_active": True,
                "role": "user",
                "password": "BrandNewP4ss!",
            },
            instance=user,
        )
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.check_password("BrandNewP4ss!")

    def test_email_synced_to_username(self):
        user = f.make_user(email="a@example.com", username="a@example.com")
        form = UserEditForm(
            data={"email": "b@example.com", "is_active": True, "role": "user", "password": ""},
            instance=user,
        )
        assert form.is_valid(), form.errors
        saved = form.save()
        assert saved.username == "b@example.com"

    def test_duplicate_email_rejected(self):
        f.make_user(email="taken@example.com")
        user = f.make_user(email="me@example.com")
        form = UserEditForm(
            data={"email": "taken@example.com", "is_active": True, "role": "user", "password": ""},
            instance=user,
        )
        assert not form.is_valid()
        assert "email" in form.errors


class TestUserEditView:
    def test_get_form_prefills_role(self, super_client, groups):
        user = f.make_user(is_staff=True)
        user.groups.add(Group.objects.get(name="Manager"))
        resp = super_client.get(reverse("dashboard:users_edit", args=[user.pk]))
        assert resp.status_code == 200
        assert resp.context["form"].initial["role"] == "manager"

    def test_edit_changes_role(self, super_client, groups):
        user = f.make_user(email="u@example.com")
        resp = super_client.post(
            reverse("dashboard:users_edit", args=[user.pk]),
            {"email": "u@example.com", "is_active": True, "role": "manager", "password": ""},
        )
        assert resp.status_code == 302
        user.refresh_from_db()
        assert user.is_staff
        assert user.groups.filter(name="Manager").exists()

    def test_requires_superuser(self, client):
        target = f.make_user()
        viewer = f.make_user(username="v", password="x", is_staff=True)
        client.force_login(viewer)
        resp = client.get(reverse("dashboard:users_edit", args=[target.pk]))
        assert resp.status_code != 200


class TestUserDeleteView:
    def test_delete_other_user(self, super_client):
        target = f.make_user(email="bye@example.com")
        resp = super_client.post(reverse("dashboard:users_delete", args=[target.pk]))
        assert resp.status_code == 302
        assert not User.objects.filter(pk=target.pk).exists()

    def test_cannot_delete_self(self, client):
        me = f.make_user(username="self", password="x", is_staff=True, is_superuser=True)
        client.force_login(me)
        resp = client.post(reverse("dashboard:users_delete", args=[me.pk]))
        assert resp.status_code == 302
        assert User.objects.filter(pk=me.pk).exists()

    def test_requires_superuser(self, client):
        target = f.make_user()
        viewer = f.make_user(username="v2", password="x", is_staff=True)
        client.force_login(viewer)
        resp = client.post(reverse("dashboard:users_delete", args=[target.pk]))
        assert resp.status_code != 302 or User.objects.filter(pk=target.pk).exists()
