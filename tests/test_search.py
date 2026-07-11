"""
Search field tests — public (frontend) and dashboard (backend).

The public navbar / home search boxes submit ``?q=`` to the tour list; the
dashboard list pages expose their own ``?q=`` search per section.
"""

import pytest
from django.urls import reverse

from tests import factories as f

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Frontend: public tour search (navbar + home "Where to?")
# ---------------------------------------------------------------------------
class TestPublicTourSearch:
    def _titles(self, response):
        return {t.title for t in response.context["tours"]}

    def test_search_by_title(self, client):
        f.make_tour(title="Samarkand Express", is_active=True)
        f.make_tour(title="Bukhara Nights", is_active=True)
        resp = client.get(reverse("tours:list") + "?q=Samarkand")
        assert resp.status_code == 200
        assert self._titles(resp) == {"Samarkand Express"}

    def test_search_by_overview(self, client):
        f.make_tour(title="Trip A", overview="Visit ancient madrasas", is_active=True)
        f.make_tour(title="Trip B", overview="Beach holiday", is_active=True)
        resp = client.get(reverse("tours:list") + "?q=madrasa")
        assert self._titles(resp) == {"Trip A"}

    def test_search_by_category_name(self, client):
        cat = f.make_tour_category(name="Mountain Adventure")
        f.make_tour(title="Peak Tour", category=cat, is_active=True)
        f.make_tour(title="City Tour", is_active=True)
        resp = client.get(reverse("tours:list") + "?q=Mountain")
        assert self._titles(resp) == {"Peak Tour"}

    def test_search_by_destination_country(self, client):
        country = f.make_country(name="Japan", is_active=True)
        tour = f.make_tour(title="Tokyo Discovery", is_active=True)
        tour.destinations.add(country)
        f.make_tour(title="Paris Walk", is_active=True)
        resp = client.get(reverse("tours:list") + "?q=Japan")
        assert self._titles(resp) == {"Tokyo Discovery"}

    def test_search_no_match_returns_empty(self, client):
        f.make_tour(title="Silk Road", is_active=True)
        resp = client.get(reverse("tours:list") + "?q=zzzznomatch")
        assert self._titles(resp) == set()

    def test_blank_query_returns_all(self, client):
        f.make_tour(title="A", is_active=True)
        f.make_tour(title="B", is_active=True)
        resp = client.get(reverse("tours:list") + "?q=")
        assert self._titles(resp) == {"A", "B"}

    def test_search_case_insensitive(self, client):
        f.make_tour(title="Khiva Tour", is_active=True)
        resp = client.get(reverse("tours:list") + "?q=khiva")
        assert self._titles(resp) == {"Khiva Tour"}

    def test_search_excludes_inactive(self, client):
        f.make_tour(title="Hidden Samarkand", is_active=False)
        resp = client.get(reverse("tours:list") + "?q=Samarkand")
        assert self._titles(resp) == set()

    def test_query_value_preserved_in_rendered_input(self, client):
        f.make_tour(title="Samarkand Express", is_active=True)
        resp = client.get(reverse("tours:list") + "?q=Samarkand")
        html = resp.content.decode()
        assert 'name="q"' in html
        assert 'value="Samarkand"' in html

    def test_search_no_duplicates_with_multiple_destinations(self, client):
        c1 = f.make_country(name="Kazakhstan", is_active=True)
        c2 = f.make_country(name="Kazakh Highlands", is_active=True)
        tour = f.make_tour(title="Central Asia", is_active=True)
        tour.destinations.add(c1, c2)
        resp = client.get(reverse("tours:list") + "?q=Kazakh")
        tours = list(resp.context["tours"])
        assert len(tours) == 1


# ---------------------------------------------------------------------------
# Home hero search form (Destination dropdown + Duration; no Date)
# ---------------------------------------------------------------------------
class TestHomeHeroSearch:
    def _titles(self, response):
        return {t.title for t in response.context["tours"]}

    def test_home_renders_destination_dropdown(self, client):
        country = f.make_country(name="Uzbekistan", is_active=True)
        resp = client.get(reverse("home"))
        html = resp.content.decode()
        assert resp.status_code == 200
        assert 'name="destination"' in html          # dropdown present
        assert 'name="departure_month"' not in html  # date field removed
        assert "Uzbekistan" in html                  # dynamic option
        assert country in list(resp.context["destinations"])

    def test_filter_by_destination(self, client):
        jp = f.make_country(name="Japan", is_active=True)
        fr = f.make_country(name="France", is_active=True)
        t1 = f.make_tour(title="Tokyo", is_active=True)
        t1.destinations.add(jp)
        t2 = f.make_tour(title="Paris", is_active=True)
        t2.destinations.add(fr)
        resp = client.get(reverse("tours:list") + f"?destination={jp.pk}")
        assert self._titles(resp) == {"Tokyo"}

    def test_filter_by_max_duration(self, client):
        f.make_tour(title="Short", duration_days=5, is_active=True)
        f.make_tour(title="Long", duration_days=20, is_active=True)
        resp = client.get(reverse("tours:list") + "?max_duration=7")
        assert self._titles(resp) == {"Short"}


# ---------------------------------------------------------------------------
# Backend: dashboard list search (staff-only)
# ---------------------------------------------------------------------------
@pytest.fixture
def admin_client(client):
    user = f.make_user(username="boss", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    return client


class TestDashboardSearch:
    def test_tours_search(self, admin_client):
        f.make_tour(title="Alpha Tour")
        f.make_tour(title="Beta Tour")
        resp = admin_client.get(reverse("dashboard:tours_list") + "?q=Alpha")
        titles = {t.title for t in resp.context["tours"]}
        assert titles == {"Alpha Tour"}

    def test_hotels_search(self, admin_client):
        f.make_hotel(name="Grand Plaza")
        f.make_hotel(name="Budget Inn")
        resp = admin_client.get(reverse("dashboard:hotels_list") + "?q=Plaza")
        names = {h.name for h in resp.context["hotels"]}
        assert names == {"Grand Plaza"}

    def test_destinations_search(self, admin_client):
        f.make_country(name="Uzbekistan")
        f.make_country(name="Kazakhstan")
        resp = admin_client.get(reverse("dashboard:destinations_list") + "?q=Uzbek")
        names = {c.name for c in resp.context["countries"]}
        assert "Uzbekistan" in names and "Kazakhstan" not in names

    def test_bookings_search_by_confirmation(self, admin_client):
        inq = f.make_inquiry(first_name="Ali", last_name="Valiev")
        f.make_inquiry(first_name="Bob", last_name="Smith")
        resp = admin_client.get(
            reverse("dashboard:bookings_list") + f"?q={inq.confirmation_number}"
        )
        pks = {b.pk for b in resp.context["bookings"]}
        assert pks == {inq.pk}

    def test_reviews_search(self, admin_client):
        f.make_review(title="Amazing trip", guest_name="Tom")
        f.make_review(title="Bad weather", guest_name="Jerry")
        resp = admin_client.get(reverse("dashboard:reviews_list") + "?q=Amazing")
        titles = {r.title for r in resp.context["reviews"]}
        assert titles == {"Amazing trip"}

    def test_dashboard_search_requires_staff(self, client):
        f.make_tour(title="Secret")
        resp = client.get(reverse("dashboard:tours_list") + "?q=Secret")
        # Anonymous users must never reach the dashboard search (redirect to
        # login, 404 from the staff guard, or 403 from the dashboard middleware).
        assert resp.status_code in (302, 403, 404)
