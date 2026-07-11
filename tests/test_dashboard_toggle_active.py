"""Tests for the dashboard quick visibility toggle (``is_active`` show/hide)."""

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from tests import factories as f

pytestmark = pytest.mark.django_db


@pytest.fixture
def super_client(client):
    user = f.make_user(username="root", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    return client


class TestToggleActive:
    def test_toggles_tour_off_and_on(self, super_client):
        tour = f.make_tour(is_active=True)
        url = reverse("dashboard:toggle_active", args=["tour", tour.pk])

        resp = super_client.post(url)
        assert resp.status_code == 302
        tour.refresh_from_db()
        assert tour.is_active is False

        super_client.post(url)
        tour.refresh_from_db()
        assert tour.is_active is True

    def test_toggles_hotel(self, super_client):
        hotel = f.make_hotel(is_active=True)
        resp = super_client.post(reverse("dashboard:toggle_active", args=["hotel", hotel.pk]))
        assert resp.status_code == 302
        hotel.refresh_from_db()
        assert hotel.is_active is False

    def test_toggles_country(self, super_client):
        country = f.make_country(name="Testland", is_active=True)
        super_client.post(reverse("dashboard:toggle_active", args=["country", country.pk]))
        country.refresh_from_db()
        assert country.is_active is False

    def test_unknown_model_404(self, super_client):
        tour = f.make_tour()
        resp = super_client.post(reverse("dashboard:toggle_active", args=["widget", tour.pk]))
        assert resp.status_code == 404

    def test_get_not_allowed(self, super_client):
        tour = f.make_tour(is_active=True)
        resp = super_client.get(reverse("dashboard:toggle_active", args=["tour", tour.pk]))
        assert resp.status_code == 405
        tour.refresh_from_db()
        assert tour.is_active is True  # unchanged

    def test_requires_staff(self, client):
        tour = f.make_tour(is_active=True)
        user = f.make_user(username="plain", password="x")
        client.force_login(user)
        resp = client.post(reverse("dashboard:toggle_active", args=["tour", tour.pk]))
        assert resp.status_code in (302, 403, 404)
        tour.refresh_from_db()
        assert tour.is_active is True  # unchanged
