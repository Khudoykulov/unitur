"""Tests for the dashboard 'Ichki Turlar' (domestic multi-city tour) section."""

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.tours.models import Tour, TourStop
from tests import factories as f

pytestmark = pytest.mark.django_db


@pytest.fixture
def super_client(client):
    user = f.make_user(username="root", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    return client


@pytest.fixture
def domestic_cities():
    """Two Uzbek cities — only these are valid itinerary stops."""
    country = f.make_country(name="Uzbekistan")
    return [
        f.make_city(name="Tashkent", country=country),
        f.make_city(name="Samarkand", country=country),
    ]


def _payload(category, stops, total=None, days=None):
    """Build a create/edit POST body: tour fields + stop & day formsets."""
    days = days or []
    data = {
        "title": "Golden Road of Uzbekistan",
        "category": category.pk,
        "duration_days": 5,
        "group_size_min": 2,
        "group_size_max": 20,
        "difficulty": "easy",
        "price_per_person": "1500.00",
        "price_currency": "USD",
        "discount_percent": 0,
        "order": 0,
        "is_active": "on",
        "stops-TOTAL_FORMS": total if total is not None else len(stops),
        "stops-INITIAL_FORMS": 0,
        "stops-MIN_NUM_FORMS": 0,
        "stops-MAX_NUM_FORMS": 1000,
        # Day-by-day itinerary formset (optional) — the real form always submits it.
        "days-TOTAL_FORMS": len(days),
        "days-INITIAL_FORMS": 0,
        "days-MIN_NUM_FORMS": 0,
        "days-MAX_NUM_FORMS": 1000,
    }
    for i, (city, order, nights) in enumerate(stops):
        data[f"stops-{i}-city"] = city.pk
        data[f"stops-{i}-order"] = order
        data[f"stops-{i}-nights"] = nights
    for i, day in enumerate(days):
        data[f"days-{i}-day_number"] = day["day_number"]
        data[f"days-{i}-title"] = day["title"]
        data[f"days-{i}-description"] = day["description"]
        data[f"days-{i}-meals_included"] = day.get("meals_included", "none")
        data[f"days-{i}-accommodation"] = day.get("accommodation", "")
        data[f"days-{i}-transport"] = day.get("transport", "")
    return data


class TestIchkiTurListView:
    def test_lists_only_multi_city_tours(self, super_client, domestic_cities):
        single = f.make_tour(title="Single city")
        f.make_tour_stop(single, order=1, city=domestic_cities[0])

        multi = f.make_tour(title="Multi city")
        f.make_tour_stop(multi, order=1, city=domestic_cities[0])
        f.make_tour_stop(multi, order=2, city=domestic_cities[1])

        resp = super_client.get(reverse("dashboard:ichki_turlar_list"))
        assert resp.status_code == 200
        titles = [t.title for t in resp.context["tours"]]
        assert "Multi city" in titles
        assert "Single city" not in titles


class TestIchkiTurCreateView:
    def test_get_form(self, super_client):
        resp = super_client.get(reverse("dashboard:ichki_turlar_create"))
        assert resp.status_code == 200
        assert "stops" in resp.context

    def test_create_with_two_stops(self, super_client, domestic_cities):
        cat = f.make_tour_category()
        data = _payload(cat, [(domestic_cities[0], 1, 2), (domestic_cities[1], 2, 1)])
        resp = super_client.post(reverse("dashboard:ichki_turlar_create"), data)
        assert resp.status_code == 302
        tour = Tour.objects.get(title="Golden Road of Uzbekistan")
        assert tour.stops.count() == 2
        assert tour.is_multi_city

    def test_create_with_days(self, super_client, domestic_cities):
        cat = f.make_tour_category()
        days = [
            {"day_number": 1, "title": "Arrival in Tashkent", "description": "City tour.",
             "meals_included": "breakfast"},
            {"day_number": 2, "title": "Samarkand", "description": "Registan visit."},
        ]
        data = _payload(
            cat, [(domestic_cities[0], 1, 2), (domestic_cities[1], 2, 1)], days=days
        )
        resp = super_client.post(reverse("dashboard:ichki_turlar_create"), data)
        assert resp.status_code == 302
        tour = Tour.objects.get(title="Golden Road of Uzbekistan")
        assert tour.days.count() == 2
        assert list(tour.days.values_list("day_number", flat=True)) == [1, 2]
        assert tour.days.first().title == "Arrival in Tashkent"

    def test_single_stop_rejected(self, super_client, domestic_cities):
        cat = f.make_tour_category()
        data = _payload(cat, [(domestic_cities[0], 1, 2)])
        before = Tour.objects.count()
        resp = super_client.post(reverse("dashboard:ichki_turlar_create"), data)
        assert resp.status_code == 200  # re-rendered with errors
        assert Tour.objects.count() == before

    def test_non_domestic_city_rejected(self, super_client, domestic_cities):
        cat = f.make_tour_category()
        foreign = f.make_city(name="Paris", country=f.make_country(name="France"))
        data = _payload(cat, [(domestic_cities[0], 1, 1), (foreign, 2, 1)])
        before = Tour.objects.count()
        resp = super_client.post(reverse("dashboard:ichki_turlar_create"), data)
        assert resp.status_code == 200
        assert Tour.objects.count() == before


class TestIchkiTurEditDelete:
    def _make_multi(self, cities):
        tour = f.make_tour(title="Editable Domestic")
        f.make_tour_stop(tour, order=1, city=cities[0])
        f.make_tour_stop(tour, order=2, city=cities[1])
        return tour

    def test_edit_updates_title(self, super_client, domestic_cities):
        tour = self._make_multi(domestic_cities)
        s1, s2 = tour.stops.all()
        data = _payload(
            f.make_tour_category(),
            [(domestic_cities[0], 1, 3), (domestic_cities[1], 2, 2)],
        )
        data["title"] = "Renamed Tour"
        data["stops-INITIAL_FORMS"] = 2
        data["stops-0-id"] = s1.pk
        data["stops-1-id"] = s2.pk
        resp = super_client.post(
            reverse("dashboard:ichki_turlar_edit", args=[tour.pk]), data
        )
        assert resp.status_code == 302
        tour.refresh_from_db()
        assert tour.title == "Renamed Tour"

    def test_delete(self, super_client, domestic_cities):
        tour = self._make_multi(domestic_cities)
        resp = super_client.post(
            reverse("dashboard:ichki_turlar_delete", args=[tour.pk])
        )
        assert resp.status_code == 302
        assert not Tour.objects.filter(pk=tour.pk).exists()
        assert not TourStop.objects.filter(tour_id=tour.pk).exists()


class TestIchkiTurPermissions:
    def test_requires_login(self, client):
        resp = client.get(reverse("dashboard:ichki_turlar_list"))
        assert resp.status_code in (302, 403, 404)

    def test_plain_user_forbidden(self, client):
        user = f.make_user(username="plain", password="x")
        client.force_login(user)
        resp = client.get(reverse("dashboard:ichki_turlar_list"))
        assert resp.status_code in (302, 403, 404)
        assert resp.status_code != 200

    def test_manager_allowed(self, client):
        Group.objects.get_or_create(name="Manager")
        mgr = f.make_user(username="mgr", password="x", is_staff=True)
        mgr.groups.add(Group.objects.get(name="Manager"))
        client.force_login(mgr)
        resp = client.get(reverse("dashboard:ichki_turlar_list"))
        assert resp.status_code == 200
