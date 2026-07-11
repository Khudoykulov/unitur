"""Tests for the dashboard CRUD on Tour Categories and Continents."""

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.destinations.models import Continent
from apps.tours.models import TourCategory
from tests import factories as f

pytestmark = pytest.mark.django_db


@pytest.fixture
def super_client(client):
    user = f.make_user(username="root", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    return client


class TestTourCategoryCRUD:
    def test_list(self, super_client):
        f.make_tour_category(name="Adventure")
        resp = super_client.get(reverse("dashboard:tour_categories_list"))
        assert resp.status_code == 200
        assert "Adventure" in resp.content.decode()

    def test_create(self, super_client):
        data = {"name": "Beach Escapes", "slug": "", "icon": "beach", "description": "Sun & sand."}
        resp = super_client.post(reverse("dashboard:tour_categories_create"), data)
        assert resp.status_code == 302
        cat = TourCategory.objects.get(name="Beach Escapes")
        assert cat.slug == "beach-escapes"  # auto-generated
        assert cat.icon == "beach"

    def test_edit(self, super_client):
        cat = f.make_tour_category(name="Cultural", icon="building")
        data = {"name": "Cultural Tours", "slug": cat.slug, "icon": "building-monument", "description": ""}
        resp = super_client.post(reverse("dashboard:tour_categories_edit", args=[cat.pk]), data)
        assert resp.status_code == 302
        cat.refresh_from_db()
        assert cat.name == "Cultural Tours"
        assert cat.icon == "building-monument"

    def test_delete(self, super_client):
        cat = f.make_tour_category(name="Temp")
        resp = super_client.post(reverse("dashboard:tour_categories_delete", args=[cat.pk]))
        assert resp.status_code == 302
        assert not TourCategory.objects.filter(pk=cat.pk).exists()

    def test_requires_staff(self, client):
        user = f.make_user(username="plain", password="x")
        client.force_login(user)
        resp = client.get(reverse("dashboard:tour_categories_list"))
        assert resp.status_code in (302, 403, 404)


class TestContinentCRUD:
    def test_list(self, super_client):
        f.make_continent(name="Antarctica")
        resp = super_client.get(reverse("dashboard:continents_list"))
        assert resp.status_code == 200
        assert "Antarctica" in resp.content.decode()

    def test_create(self, super_client):
        resp = super_client.post(reverse("dashboard:continents_create"), {"name": "Oceania", "slug": ""})
        assert resp.status_code == 302
        cont = Continent.objects.get(name="Oceania")
        assert cont.slug == "oceania"

    def test_edit(self, super_client):
        cont = f.make_continent(name="Eurasia")
        resp = super_client.post(
            reverse("dashboard:continents_edit", args=[cont.pk]), {"name": "Europe", "slug": cont.slug}
        )
        assert resp.status_code == 302
        cont.refresh_from_db()
        assert cont.name == "Europe"

    def test_delete(self, super_client):
        cont = f.make_continent(name="Scrap")
        resp = super_client.post(reverse("dashboard:continents_delete", args=[cont.pk]))
        assert resp.status_code == 302
        assert not Continent.objects.filter(pk=cont.pk).exists()

    def test_manager_allowed(self, client):
        Group.objects.get_or_create(name="Manager")
        mgr = f.make_user(username="mgr", password="x", is_staff=True)
        mgr.groups.add(Group.objects.get(name="Manager"))
        client.force_login(mgr)
        resp = client.get(reverse("dashboard:continents_list"))
        assert resp.status_code == 200
