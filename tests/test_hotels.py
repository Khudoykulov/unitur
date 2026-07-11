"""Tests for the hotels app models."""

import pytest
from django.urls import reverse

from tests import factories as f

pytestmark = pytest.mark.django_db


class TestHotelAmenity:
    def test_str(self):
        a = f.make_amenity(name="Free WiFi")
        assert str(a) == "Free WiFi"


class TestHotel:
    def test_str_and_slug(self):
        hotel = f.make_hotel(name="Hyatt Regency")
        assert str(hotel) == "Hyatt Regency"
        assert hotel.slug == "hyatt-regency"

    def test_get_absolute_url(self):
        hotel = f.make_hotel(name="Hilton", slug="hilton")
        assert hotel.get_absolute_url() == reverse(
            "hotels:detail", kwargs={"slug": "hilton"}
        )

    @pytest.mark.parametrize(
        "stars,expected",
        [
            (5, "★★★★★"),
            (3, "★★★☆☆"),
            (1, "★☆☆☆☆"),
        ],
    )
    def test_star_display(self, stars, expected):
        hotel = f.make_hotel(stars=stars)
        assert hotel.star_display == expected


class TestHotelRoom:
    def test_str_uses_room_type_display(self):
        hotel = f.make_hotel(name="Plaza")
        room = f.make_room(hotel=hotel, room_type="suite")
        assert str(room) == "Plaza – Suite"

    def test_default_room_type(self):
        room = f.make_room()
        assert room.room_type == "double"
        assert room.is_available is True
