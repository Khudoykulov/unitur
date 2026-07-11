"""Tests for the dashboard domestic-cities section and the IchkiTur form."""

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.dashboard.forms import IchkiTurForm
from apps.destinations.models import City
from tests import factories as f

pytestmark = pytest.mark.django_db


@pytest.fixture
def super_client(client):
    user = f.make_user(username="root", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    return client


@pytest.fixture
def uzbekistan():
    return f.make_country(name="Uzbekistan")


class TestIchkiTurForm:
    def test_no_difficulty_field(self):
        assert "difficulty" not in IchkiTurForm().fields


class TestDomesticCityCreate:
    def test_create_attaches_to_uzbekistan(self, super_client, uzbekistan):
        resp = super_client.post(
            reverse("dashboard:cities_create"),
            {"name": "Khiva", "overview": "Ancient walled city.", "order": 0, "is_active": "on"},
        )
        assert resp.status_code == 302
        city = City.objects.get(name="Khiva")
        assert city.country == uzbekistan

    def test_list_only_domestic(self, super_client, uzbekistan):
        f.make_city(name="Bukhara", country=uzbekistan)
        f.make_city(name="Paris", country=f.make_country(name="France"))
        resp = super_client.get(reverse("dashboard:cities_list"))
        assert resp.status_code == 200
        names = [c.name for c in resp.context["cities"]]
        assert "Bukhara" in names
        assert "Paris" not in names

    def test_edit(self, super_client, uzbekistan):
        city = f.make_city(name="Nukus", country=uzbekistan)
        resp = super_client.post(
            reverse("dashboard:cities_edit", args=[city.pk]),
            {"name": "Nukus City", "overview": "", "order": 1, "is_active": "on"},
        )
        assert resp.status_code == 302
        city.refresh_from_db()
        assert city.name == "Nukus City"

    def test_delete(self, super_client, uzbekistan):
        city = f.make_city(name="Termez", country=uzbekistan)
        resp = super_client.post(reverse("dashboard:cities_delete", args=[city.pk]))
        assert resp.status_code == 302
        assert not City.objects.filter(pk=city.pk).exists()

    def test_cannot_edit_non_domestic(self, super_client, uzbekistan):
        foreign = f.make_city(name="Rome", country=f.make_country(name="Italy"))
        resp = super_client.get(reverse("dashboard:cities_edit", args=[foreign.pk]))
        assert resp.status_code == 404

    def test_list_works_when_language_is_uzbek(self, super_client, uzbekistan):
        """Regression: switching the panel to Uzbek must not hide the cities.

        ``country__name`` resolves to name_uz under modeltranslation, which for
        Uzbekistan is "O'zbekiston" (no "Uzbek"); the filter must use name_en.
        """
        f.make_city(name="Bukhara", country=uzbekistan)
        super_client.cookies["django_language"] = "uz"
        resp = super_client.get(reverse("dashboard:cities_list"))
        assert resp.status_code == 200
        assert "Bukhara" in [c.name for c in resp.context["cities"]]


class TestDomesticCityPermissions:
    def test_plain_user_forbidden(self, client):
        user = f.make_user(username="plain", password="x")
        client.force_login(user)
        resp = client.get(reverse("dashboard:cities_list"))
        assert resp.status_code != 200

    def test_manager_allowed(self, client):
        Group.objects.get_or_create(name="Manager")
        mgr = f.make_user(username="mgr", password="x", is_staff=True)
        mgr.groups.add(Group.objects.get(name="Manager"))
        client.force_login(mgr)
        resp = client.get(reverse("dashboard:cities_list"))
        assert resp.status_code == 200


class TestAddUzbekCitiesCommand:
    def test_creates_cities_under_uzbekistan(self, uzbekistan):
        from django.core.management import call_command
        call_command("add_uzbek_cities", no_images=True, no_translate=True)
        assert City.objects.filter(country=uzbekistan, name="Samarkand").exists()
        assert City.objects.filter(country=uzbekistan, name="Khiva").exists()
        assert City.objects.filter(country=uzbekistan).count() >= 14

    def test_idempotent(self, uzbekistan):
        from django.core.management import call_command
        call_command("add_uzbek_cities", no_images=True, no_translate=True)
        n1 = City.objects.filter(country=uzbekistan).count()
        call_command("add_uzbek_cities", no_images=True, no_translate=True)
        n2 = City.objects.filter(country=uzbekistan).count()
        assert n1 == n2
