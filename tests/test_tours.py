"""Tests for the tours app models and business logic."""

from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.urls import reverse

from apps.tours.filters import TourFilter
from apps.tours.models import Tour, TourDay, TourStop
from tests import factories as f

pytestmark = pytest.mark.django_db


class TestTourCategory:
    def test_str_and_slug(self):
        cat = f.make_tour_category(name="Adventure Trips")
        assert str(cat) == "Adventure Trips"
        assert cat.slug == "adventure-trips"

    def test_get_absolute_url(self):
        cat = f.make_tour_category(name="Beach", slug="beach")
        assert cat.get_absolute_url() == reverse("tours:list") + "?category=beach"


class TestTourCategoryFilter:
    """The site links categories by slug, so the filter must match by slug
    (regression: it previously used the default pk and never matched)."""

    def test_filter_by_slug_matches(self):
        beach = f.make_tour_category(name="Beach", slug="beach")
        culture = f.make_tour_category(name="Culture", slug="culture")
        t1 = f.make_tour(title="Seaside", category=beach)
        f.make_tour(title="Museums", category=culture)

        result = TourFilter({"category": "beach"}, queryset=Tour.objects.all()).qs
        assert list(result) == [t1]

    def test_filter_by_unknown_slug_is_ignored(self):
        # An unknown slug is an invalid choice, so django-filter drops the
        # filter and lists everything rather than erroring — a graceful fallback.
        beach = f.make_tour_category(name="Beach", slug="beach")
        f.make_tour(title="Seaside", category=beach)
        result = TourFilter({"category": "does-not-exist"}, queryset=Tour.objects.all()).qs
        assert result.count() == 1

    def test_view_category_slug_filters(self, client):
        beach = f.make_tour_category(name="Beach", slug="beach")
        culture = f.make_tour_category(name="Culture", slug="culture")
        f.make_tour(title="Seaside Escape", category=beach, is_active=True)
        f.make_tour(title="City Museums", category=culture, is_active=True)

        resp = client.get(reverse("tours:list"), {"category": "beach"})
        assert resp.status_code == 200
        titles = [t.title for t in resp.context["tours"]]
        assert "Seaside Escape" in titles
        assert "City Museums" not in titles


class TestTourListSeparation:
    """/tours/ shows only single-city (international) tours; multi-city
    "Ichki Turlar" live on their own page. cache_page is cleared per test so
    each request renders fresh (and exposes response.context)."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        from django.core.cache import cache
        cache.clear()
        yield
        cache.clear()

    def test_tours_list_excludes_multi_city(self, client):
        single = f.make_tour(title="Japan Highlights", is_active=True)
        f.make_tour_stop(single, order=1)  # one stop → still single-city
        multi = f.make_tour(title="Uzbek Grand Tour", is_active=True)
        f.make_tour_stop(multi, order=1)
        f.make_tour_stop(multi, order=2)

        resp = client.get(reverse("tours:list"))
        titles = [t.title for t in resp.context["tours"]]
        assert "Japan Highlights" in titles
        assert "Uzbek Grand Tour" not in titles

    def test_tours_list_includes_zero_stop_tours(self, client):
        plain = f.make_tour(title="No Stops Intl", is_active=True)
        resp = client.get(reverse("tours:list"))
        assert plain.title in [t.title for t in resp.context["tours"]]

    def test_count_unaffected_by_reviews_fanout(self, client):
        # A single-city tour with several reviews must still count as 1 stop
        # (distinct=True guards against the review join inflating num_stops).
        tour = f.make_tour(title="Reviewed Single", is_active=True)
        f.make_tour_stop(tour, order=1)
        f.make_review(tour=tour, rating=5, status="approved")
        f.make_review(tour=tour, rating=4, status="approved")

        resp = client.get(reverse("tours:list"))
        assert "Reviewed Single" in [t.title for t in resp.context["tours"]]

    def test_ichki_turlar_only_multi_city(self, client):
        single = f.make_tour(title="Single City", is_active=True)
        f.make_tour_stop(single, order=1)
        multi = f.make_tour(title="Multi City", is_active=True)
        f.make_tour_stop(multi, order=1)
        f.make_tour_stop(multi, order=2)

        resp = client.get(reverse("ichki-turlar-list"))
        titles = [t.title for t in resp.context["tours"]]
        assert "Multi City" in titles
        assert "Single City" not in titles


class TestTour:
    def test_str_and_slug(self):
        tour = f.make_tour(title="Silk Road Journey")
        assert str(tour) == "Silk Road Journey"
        assert tour.slug == "silk-road-journey"

    def test_get_absolute_url(self):
        tour = f.make_tour(title="Desert Tour", slug="desert-tour")
        assert tour.get_absolute_url() == reverse(
            "tours:detail", kwargs={"slug": "desert-tour"}
        )

    def test_discounted_price_no_discount(self):
        tour = f.make_tour(price_per_person=Decimal("1000"), discount_percent=0)
        assert tour.discounted_price == Decimal("1000")

    def test_discounted_price_with_discount(self):
        tour = f.make_tour(price_per_person=Decimal("1000"), discount_percent=25)
        assert tour.discounted_price == Decimal("750.00")

    def test_average_rating_no_reviews(self):
        tour = f.make_tour()
        assert tour.average_rating == 0.0

    def test_average_rating_only_approved(self):
        tour = f.make_tour()
        f.make_review(tour=tour, rating=4, status="approved")
        f.make_review(tour=tour, rating=2, status="approved")
        f.make_review(tour=tour, rating=5, status="pending")  # ignored
        assert tour.average_rating == 3.0

    def test_increment_views(self):
        tour = f.make_tour()
        assert tour.views_count == 0
        tour.increment_views()
        tour.refresh_from_db()
        assert tour.views_count == 1

    def test_is_multi_city_false_with_one_stop(self):
        tour = f.make_tour()
        f.make_tour_stop(tour, order=1)
        assert tour.is_multi_city is False

    def test_is_multi_city_true_with_two_stops(self):
        tour = f.make_tour()
        f.make_tour_stop(tour, order=1)
        f.make_tour_stop(tour, order=2)
        assert tour.is_multi_city is True


class TestTourStop:
    def test_str(self):
        tour = f.make_tour(title="Grand Tour")
        city = f.make_city(name="Bukhara")
        stop = f.make_tour_stop(tour, order=2, city=city)
        assert str(stop) == "Grand Tour – 2. Bukhara"

    def test_unique_order_per_tour(self):
        tour = f.make_tour()
        f.make_tour_stop(tour, order=1)
        with pytest.raises(IntegrityError):
            f.make_tour_stop(tour, order=1)


class TestTourDay:
    def test_str(self):
        tour = f.make_tour()
        day = TourDay.objects.create(
            tour=tour, day_number=3, title="Mountain Hike", description="..."
        )
        assert str(day) == "Day 3: Mountain Hike"

    def test_tour_days_ordering(self):
        tour = f.make_tour()
        d2 = TourDay.objects.create(tour=tour, day_number=2, title="B", description="y")
        d1 = TourDay.objects.create(tour=tour, day_number=1, title="A", description="x")
        assert list(tour.days.all()) == [d1, d2]


class TestTourDeparture:
    def test_str(self):
        tour = f.make_tour(title="Trek")
        dep = f.make_departure(tour=tour)
        assert str(dep).startswith("Trek – ")

    def test_seats_left(self):
        dep = f.make_departure(available_seats=20, booked_seats=5)
        assert dep.seats_left == 15

    def test_seats_left_never_negative(self):
        dep = f.make_departure(available_seats=5, booked_seats=10)
        assert dep.seats_left == 0

    def test_effective_price_uses_override(self):
        tour = f.make_tour(price_per_person=Decimal("1000"))
        dep = f.make_departure(tour=tour, price_override=Decimal("800"))
        assert dep.effective_price == Decimal("800")

    def test_effective_price_falls_back_to_discounted(self):
        tour = f.make_tour(price_per_person=Decimal("1000"), discount_percent=10)
        dep = f.make_departure(tour=tour, price_override=None)
        assert dep.effective_price == Decimal("900.0")

    def test_is_bookable_open_with_seats(self):
        dep = f.make_departure(status="open", available_seats=10, booked_seats=0)
        assert dep.is_bookable() is True

    def test_is_bookable_false_when_closed(self):
        dep = f.make_departure(status="closed", available_seats=10, booked_seats=0)
        assert dep.is_bookable() is False

    def test_is_bookable_false_when_full(self):
        dep = f.make_departure(status="open", available_seats=10, booked_seats=10)
        assert dep.is_bookable() is False


class TestTourDetailPostReview:
    def test_post_tour_review_success(self, client):
        tour = f.make_tour(slug="samarqand-safari")
        url = reverse("tours:detail", kwargs={"slug": tour.slug})
        resp = client.post(url, {
            "guest_name": "Diyorbek",
            "rating": "5",
            "body": "Ajoyib sayohat bo'ldi!",
        })
        assert resp.status_code == 302
        assert resp.url == tour.get_absolute_url() + "#reviews-section"
        review = tour.reviews.first()
        assert review is not None
        assert review.guest_name == "Diyorbek"
        assert review.rating == 5
        assert review.body == "Ajoyib sayohat bo'ldi!"
