"""
Lightweight factory helpers for building model instances in tests.

These avoid external image/file dependencies (all ImageFields are left blank)
so tests run fast and require no media on disk.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model

from apps.bookings.models import Inquiry
from apps.destinations.models import Attraction, City, Continent, Country
from apps.guides.models import Article, GuideCategory, Tag
from apps.hotels.models import Hotel, HotelAmenity, HotelRoom
from apps.reviews.models import Review
from apps.tours.models import (
    Tour,
    TourCategory,
    TourDeparture,
    TourStop,
)

User = get_user_model()

_counter = {"n": 0}


def _uniq() -> int:
    _counter["n"] += 1
    return _counter["n"]


def make_user(**kwargs) -> "User":
    n = _uniq()
    defaults = {
        "username": f"user{n}",
        "email": f"user{n}@example.com",
        "password": "pass12345",
    }
    defaults.update(kwargs)
    password = defaults.pop("password")
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def make_continent(**kwargs) -> Continent:
    defaults = {"name": f"Continent {_uniq()}"}
    defaults.update(kwargs)
    return Continent.objects.create(**defaults)


def make_country(**kwargs) -> Country:
    if "continent" not in kwargs:
        kwargs["continent"] = make_continent()
    defaults = {"name": f"Country {_uniq()}"}
    defaults.update(kwargs)
    return Country.objects.create(**defaults)


def make_city(**kwargs) -> City:
    if "country" not in kwargs:
        kwargs["country"] = make_country()
    defaults = {"name": f"City {_uniq()}"}
    defaults.update(kwargs)
    return City.objects.create(**defaults)


def make_attraction(**kwargs) -> Attraction:
    if "city" not in kwargs:
        kwargs["city"] = make_city()
    defaults = {"name": f"Attraction {_uniq()}"}
    defaults.update(kwargs)
    return Attraction.objects.create(**defaults)


def make_tour_category(**kwargs) -> TourCategory:
    defaults = {"name": f"Category {_uniq()}"}
    defaults.update(kwargs)
    return TourCategory.objects.create(**defaults)


def make_tour(**kwargs) -> Tour:
    if "category" not in kwargs:
        kwargs["category"] = make_tour_category()
    defaults = {
        "title": f"Tour {_uniq()}",
        "price_per_person": Decimal("1000.00"),
    }
    defaults.update(kwargs)
    return Tour.objects.create(**defaults)


def make_tour_stop(tour: Tour, order: int, city: City | None = None, **kwargs) -> TourStop:
    return TourStop.objects.create(
        tour=tour, city=city or make_city(), order=order, **kwargs
    )


def make_departure(tour: Tour | None = None, **kwargs) -> TourDeparture:
    tour = tour or make_tour()
    defaults = {
        "departure_date": date.today() + timedelta(days=30),
        "return_date": date.today() + timedelta(days=37),
        "available_seats": 20,
        "booked_seats": 0,
    }
    defaults.update(kwargs)
    return TourDeparture.objects.create(tour=tour, **defaults)


def make_amenity(**kwargs) -> HotelAmenity:
    defaults = {"name": f"Amenity {_uniq()}"}
    defaults.update(kwargs)
    return HotelAmenity.objects.create(**defaults)


def make_hotel(**kwargs) -> Hotel:
    if "city" not in kwargs:
        kwargs["city"] = make_city()
    defaults = {"name": f"Hotel {_uniq()}"}
    defaults.update(kwargs)
    return Hotel.objects.create(**defaults)


def make_room(hotel: Hotel | None = None, **kwargs) -> HotelRoom:
    hotel = hotel or make_hotel()
    return HotelRoom.objects.create(hotel=hotel, **kwargs)


def make_guide_category(**kwargs) -> GuideCategory:
    defaults = {"name": f"Guide Cat {_uniq()}"}
    defaults.update(kwargs)
    return GuideCategory.objects.create(**defaults)


def make_tag(**kwargs) -> Tag:
    defaults = {"name": f"Tag {_uniq()}"}
    defaults.update(kwargs)
    return Tag.objects.create(**defaults)


def make_article(**kwargs) -> Article:
    defaults = {
        "title": f"Article {_uniq()}",
        "content": "Body content.",
    }
    defaults.update(kwargs)
    return Article.objects.create(**defaults)


def make_review(**kwargs) -> Review:
    defaults = {
        "title": f"Review {_uniq()}",
        "body": "Great trip.",
        "rating": 5,
    }
    defaults.update(kwargs)
    return Review.objects.create(**defaults)


def make_inquiry(**kwargs) -> Inquiry:
    defaults = {
        "first_name": "Ali",
        "last_name": "Valiev",
        "phone": "+998901234567",
    }
    defaults.update(kwargs)
    return Inquiry.objects.create(**defaults)
