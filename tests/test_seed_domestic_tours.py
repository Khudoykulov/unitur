"""Tests for the ``seed_domestic_tours`` management command."""

import io

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db.models import Count

from apps.destinations.models import City, Country
from apps.tours.models import Tour
from tests import factories as f

pytestmark = pytest.mark.django_db


def _jpeg_bytes(color="blue"):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (12, 8), color).save(buf, "JPEG")
    return buf.getvalue()


@pytest.fixture
def uzbekistan():
    return f.make_country(name="Uzbekistan")


def _multi_city_count():
    return Tour.objects.annotate(n=Count("stops")).filter(n__gt=1).count()


def test_creates_multi_city_tours(uzbekistan):
    call_command("seed_domestic_tours", verbosity=0)
    assert _multi_city_count() == 5
    # Every seeded tour has an ordered, multi-stop itinerary.
    golden = Tour.objects.get(slug="golden-road-of-uzbekistan")
    assert list(golden.stops.values_list("order", flat=True)) == [1, 2, 3, 4]
    # Missing Uzbek cities were created and attached to Uzbekistan.
    assert City.objects.filter(name="Bukhara", country=uzbekistan).exists()


def test_is_idempotent(uzbekistan):
    call_command("seed_domestic_tours", verbosity=0)
    tours_after_first = Tour.objects.count()
    cities_after_first = City.objects.count()

    call_command("seed_domestic_tours", verbosity=0)
    assert Tour.objects.count() == tours_after_first
    assert City.objects.count() == cities_after_first


def test_aborts_without_uzbekistan():
    # No Uzbekistan country in the DB → nothing is created.
    assert not Country.objects.filter(name_en__icontains="Uzbek").exists()
    call_command("seed_domestic_tours", verbosity=0)
    assert Tour.objects.count() == 0


class TestSetDomesticTourCovers:
    def test_copies_signature_city_cover(self, uzbekistan, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        samarkand = f.make_city(name="Samarkand", country=uzbekistan)
        samarkand.cover_image.save(
            "samarkand-cover.jpg", ContentFile(_jpeg_bytes()), save=True
        )
        call_command("seed_domestic_tours", verbosity=0)

        call_command("set_domestic_tour_covers", verbosity=0)

        golden = Tour.objects.get(slug="golden-road-of-uzbekistan")
        assert golden.cover_image  # Samarkand is its signature city
        assert "golden-road-of-uzbekistan-cover" in golden.cover_image.name

    def test_skips_tour_that_already_has_cover(self, uzbekistan, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        samarkand = f.make_city(name="Samarkand", country=uzbekistan)
        samarkand.cover_image.save("s.jpg", ContentFile(_jpeg_bytes()), save=True)
        call_command("seed_domestic_tours", verbosity=0)

        golden = Tour.objects.get(slug="golden-road-of-uzbekistan")
        golden.cover_image.save("existing.jpg", ContentFile(_jpeg_bytes("red")), save=True)

        call_command("set_domestic_tour_covers", verbosity=0)
        golden.refresh_from_db()
        assert golden.cover_image.name.endswith("existing.jpg")  # untouched

    def test_missing_source_leaves_no_cover(self, uzbekistan, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        # No city has a cover image → command runs but sets nothing.
        call_command("seed_domestic_tours", verbosity=0)
        call_command("set_domestic_tour_covers", verbosity=0)
        assert not Tour.objects.get(slug="golden-road-of-uzbekistan").cover_image
