"""
Smoke / integration tests for public views.

These render real templates against the test database, catching template
errors, broken context, and reverse() mismatches.
"""

import json

import pytest
from django.urls import reverse

from apps.bookings.models import Inquiry
from tests import factories as f

pytestmark = pytest.mark.django_db


class TestStaticPages:
    def test_home(self, client):
        assert client.get(reverse("home")).status_code == 200

    def test_about(self, client):
        assert client.get(reverse("about")).status_code == 200

    def test_contact(self, client):
        assert client.get(reverse("contact")).status_code == 200

    def test_robots_txt(self, client):
        resp = client.get("/robots.txt")
        assert resp.status_code == 200
        assert b"Sitemap:" in resp.content

    def test_sitemap(self, client):
        f.make_tour(is_active=True)
        resp = client.get("/sitemap.xml")
        assert resp.status_code == 200


class TestTourViews:
    def test_list(self, client):
        f.make_tour(is_active=True)
        assert client.get(reverse("tours:list")).status_code == 200

    def test_list_with_sort(self, client):
        f.make_tour(is_active=True)
        assert client.get(reverse("tours:list") + "?sort=price_asc").status_code == 200

    def test_detail(self, client):
        tour = f.make_tour(is_active=True, slug="my-tour")
        resp = client.get(reverse("tours:detail", kwargs={"slug": "my-tour"}))
        assert resp.status_code == 200

    def test_detail_increments_views(self, client):
        tour = f.make_tour(is_active=True, slug="viewed-tour")
        client.get(reverse("tours:detail", kwargs={"slug": "viewed-tour"}))
        tour.refresh_from_db()
        assert tour.views_count == 1

    def test_detail_inactive_404(self, client):
        f.make_tour(is_active=False, slug="hidden")
        resp = client.get(reverse("tours:detail", kwargs={"slug": "hidden"}))
        assert resp.status_code == 404

    def test_ichki_turlar_list(self, client):
        tour = f.make_tour(is_active=True)
        f.make_tour_stop(tour, order=1)
        f.make_tour_stop(tour, order=2)
        assert client.get(reverse("ichki-turlar-list")).status_code == 200


class TestDestinationViews:
    def test_list(self, client):
        f.make_country(is_active=True)
        assert client.get(reverse("destinations:list")).status_code == 200

    def test_country_detail(self, client):
        country = f.make_country(is_active=True, slug="uzbekistan")
        resp = client.get(reverse("destinations:country", kwargs={"slug": "uzbekistan"}))
        assert resp.status_code == 200

    def test_city_detail(self, client):
        country = f.make_country(is_active=True, slug="uzbekistan")
        city = f.make_city(country=country, is_active=True, slug="samarkand")
        resp = client.get(
            reverse(
                "destinations:city",
                kwargs={"country_slug": "uzbekistan", "city_slug": "samarkand"},
            )
        )
        assert resp.status_code == 200


class TestCityInfoAPI:
    def test_returns_city_data(self, client):
        city = f.make_city(name="Khiva", is_active=True, slug="khiva", overview="Old city")
        f.make_attraction(city=city, name="Itchan Kala", is_active=True)
        resp = client.get(reverse("city-info-api", kwargs={"slug": "khiva"}))
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["name"] == "Khiva"
        assert data["description"] == "Old city"
        assert any(a["name"] == "Itchan Kala" for a in data["attractions"])

    def test_not_found(self, client):
        resp = client.get(reverse("city-info-api", kwargs={"slug": "nope"}))
        assert resp.status_code == 404


class TestHotelViews:
    def test_list(self, client):
        f.make_hotel(is_active=True)
        assert client.get(reverse("hotels:list")).status_code == 200

    def test_detail(self, client):
        f.make_hotel(is_active=True, slug="grand-hotel")
        resp = client.get(reverse("hotels:detail", kwargs={"slug": "grand-hotel"}))
        assert resp.status_code == 200


class TestGuideViews:
    def test_list(self, client):
        f.make_article(is_published=True, is_active=True)
        assert client.get(reverse("guides:list")).status_code == 200

    def test_detail(self, client):
        f.make_article(is_published=True, is_active=True, slug="my-guide")
        resp = client.get(reverse("guides:detail", kwargs={"slug": "my-guide"}))
        assert resp.status_code == 200

    def test_by_category(self, client):
        cat = f.make_guide_category(slug="tips")
        f.make_article(category=cat, is_published=True, is_active=True)
        resp = client.get(reverse("guides:by_category", kwargs={"slug": "tips"}))
        assert resp.status_code == 200


class TestReviewViews:
    def test_list(self, client):
        f.make_review(status="approved", review_type="general")
        assert client.get(reverse("reviews:list")).status_code == 200

    def test_list_filtered(self, client):
        f.make_review(status="approved", review_type="tour", rating=5)
        resp = client.get(reverse("reviews:list") + "?type=tour&rating=5")
        assert resp.status_code == 200


class TestBookingFlow:
    def test_booking_form_get(self, client):
        f.make_tour(is_active=True, slug="book-me")
        resp = client.get(reverse("bookings:book", kwargs={"slug": "book-me"}))
        assert resp.status_code == 200

    def test_booking_form_post_creates_inquiry(self, client):
        tour = f.make_tour(is_active=True, slug="book-me")
        resp = client.post(
            reverse("bookings:book", kwargs={"slug": "book-me"}),
            {
                "tour": tour.pk,
                "first_name": "Ali",
                "last_name": "Valiev",
                "phone": "+998901112233",
            },
        )
        assert resp.status_code == 302
        inquiry = Inquiry.objects.get(first_name="Ali")
        assert inquiry.inquiry_type == "tour"
        assert inquiry.source == "web"

    def test_confirmation_page(self, client):
        inquiry = f.make_inquiry()
        resp = client.get(reverse("bookings:confirmation", kwargs={"pk": inquiry.pk}))
        assert resp.status_code == 200

    def test_inquiry_form_get(self, client):
        assert client.get(reverse("bookings:inquiry")).status_code == 200

    def test_inquiry_form_post(self, client):
        resp = client.post(
            reverse("bookings:inquiry"),
            {
                "inquiry_type": "custom",
                "first_name": "Ali",
                "last_name": "Valiev",
                "phone": "+998901112233",
                "num_adults": 2,
                "num_children": 0,
            },
        )
        assert resp.status_code == 302
        assert Inquiry.objects.filter(first_name="Ali").exists()
