"""Tests for the accounts app: UserProfile, AdminLoginLog, staff login."""

import pytest
from django.urls import reverse

from apps.accounts.models import AdminLoginLog, UserProfile
from apps.accounts.views import _get_client_ip
from django.test import RequestFactory
from tests import factories as f

pytestmark = pytest.mark.django_db


class TestUserProfile:
    def test_str(self):
        user = f.make_user(username="ali")
        profile = UserProfile.objects.create(user=user)
        assert str(profile) == f"Profile of {user}"

    def test_get_absolute_url(self):
        user = f.make_user()
        profile = UserProfile.objects.create(user=user)
        assert profile.get_absolute_url() == reverse("accounts:profile")


class TestAdminLoginLog:
    def test_str(self):
        user = f.make_user(username="staff")
        log = AdminLoginLog.objects.create(user=user, ip_address="1.2.3.4")
        assert str(log).startswith(str(user))


class TestClientIpHelper:
    def test_x_forwarded_for_priority(self):
        req = RequestFactory().get("/")
        req.META["HTTP_X_FORWARDED_FOR"] = "9.9.9.9, 1.1.1.1"
        assert _get_client_ip(req) == "9.9.9.9"

    def test_x_real_ip(self):
        req = RequestFactory().get("/", HTTP_X_REAL_IP="8.8.8.8")
        assert _get_client_ip(req) == "8.8.8.8"

    def test_remote_addr_fallback(self):
        req = RequestFactory().get("/", REMOTE_ADDR="7.7.7.7")
        assert _get_client_ip(req) == "7.7.7.7"


class TestStaffLoginView:
    def test_get_redirects_home(self, client):
        resp = client.get(reverse("accounts:staff-login"))
        assert resp.status_code == 302

    def test_post_valid_staff_logs_in(self, client):
        user = f.make_user(username="boss", password="secret123", is_staff=True)
        resp = client.post(
            reverse("accounts:staff-login"),
            {"username": "boss", "password": "secret123"},
        )
        assert resp.status_code == 302
        assert AdminLoginLog.objects.filter(user=user).exists()

    def test_post_non_staff_rejected(self, client):
        f.make_user(username="reg", password="secret123", is_staff=False)
        resp = client.post(
            reverse("accounts:staff-login"),
            {"username": "reg", "password": "secret123"},
        )
        assert resp.status_code == 302
        assert AdminLoginLog.objects.count() == 0

    def test_post_wrong_password_rejected(self, client):
        f.make_user(username="boss", password="secret123", is_staff=True)
        resp = client.post(
            reverse("accounts:staff-login"),
            {"username": "boss", "password": "WRONG"},
        )
        assert resp.status_code == 302
        assert AdminLoginLog.objects.count() == 0
