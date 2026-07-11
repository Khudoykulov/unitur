"""Seed a handful of realistic domestic ("Ichki Turlar") multi-city tours.

Domestic tours are ordinary :class:`~apps.tours.models.Tour` objects that have
more than one :class:`~apps.tours.models.TourStop` (that is what makes them
"multi-city" and lists them on ``/ichki-turlar/``). This command:

* ensures a canonical set of Uzbek cities exists (creating any that are
  missing, attached to Uzbekistan), and
* creates the sample tours together with their ordered stops.

It is **idempotent** — tours and cities are matched by name/slug, so re-running
it neither duplicates data nor overwrites tours that already exist. Run with::

    python manage.py seed_domestic_tours
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.destinations.models import City, Country
from apps.tours.models import Tour, TourCategory, TourStop

# name -> short overview, for any Uzbek city we need but don't have yet.
CITIES = {
    "Tashkent": "Uzbekistan's vibrant capital, blending Soviet-era avenues with modern life.",
    "Samarkand": "The Registan and Timurid monuments make this the jewel of the Silk Road.",
    "Bukhara": "A living museum city with madrasas, minarets and covered bazaars.",
    "Khiva": "The walled inner city of Itchan Kala, frozen in time.",
    "Shakhrisabz": "Birthplace of Amir Timur, home to the ruins of the Ak-Saray Palace.",
    "Nurata": "Gateway to the Kyzylkum desert, yurt camps and Aydarkul Lake.",
    "Kokand": "Former khanate capital in the Fergana Valley, rich in palaces.",
    "Fergana": "Heart of the fertile Fergana Valley, famed for silk and ceramics.",
}

# Each tour: slug -> spec. ``route`` is a list of (city_name, nights) in order.
TOURS = [
    {
        "slug": "golden-road-of-uzbekistan",
        "title": "Golden Road of Uzbekistan",
        "category": "cultural",
        "price": "1450.00",
        "route": [("Tashkent", 1), ("Samarkand", 2), ("Bukhara", 2), ("Khiva", 1)],
        "overview": "The classic Silk Road journey across Uzbekistan's four great "
                    "cities — from the capital Tashkent to the walled city of Khiva.",
    },
    {
        "slug": "samarkand-bukhara-highlights",
        "title": "Samarkand & Bukhara Highlights",
        "category": "cultural",
        "price": "890.00",
        "route": [("Samarkand", 2), ("Bukhara", 2)],
        "overview": "A short, rich introduction to Uzbekistan's two most iconic "
                    "Silk Road cities.",
    },
    {
        "slug": "silk-road-explorer",
        "title": "Silk Road Explorer",
        "category": "cultural",
        "price": "990.00",
        "route": [("Tashkent", 1), ("Samarkand", 2), ("Bukhara", 1)],
        "overview": "Follow the ancient trade route from Tashkent through Samarkand "
                    "to Bukhara.",
    },
    {
        "slug": "ancient-khorezm-khiva-bukhara",
        "title": "Ancient Khorezm: Khiva & Bukhara",
        "category": "cultural",
        "price": "1050.00",
        "route": [("Khiva", 2), ("Bukhara", 2)],
        "overview": "Explore the desert cities of ancient Khorezm, from the "
                    "open-air museum of Khiva to the bazaars of Bukhara.",
    },
    {
        "slug": "fergana-valley-discovery",
        "title": "Fergana Valley Discovery",
        "category": "cultural",
        "price": "760.00",
        "route": [("Tashkent", 1), ("Kokand", 1), ("Fergana", 2)],
        "overview": "Discover the crafts, silk and ceramics of the lush Fergana "
                    "Valley beyond the usual Silk Road trail.",
    },
]


class Command(BaseCommand):
    help = "Seed sample domestic (multi-city / Ichki Turlar) tours."

    @transaction.atomic
    def handle(self, *args, **options):
        uz = Country.objects.filter(name_en__icontains="Uzbek").first()
        if uz is None:
            self.stderr.write(self.style.ERROR(
                "No Uzbekistan country found (name_en contains 'Uzbek'); aborting."
            ))
            return

        cities = self._ensure_cities(uz)
        category_cache: dict[str, TourCategory] = {}
        created_tours = skipped_tours = 0

        for spec in TOURS:
            tour, created = Tour.objects.get_or_create(
                slug=spec["slug"],
                defaults={
                    "title": spec["title"],
                    "category": self._category(spec["category"], category_cache),
                    "price_per_person": Decimal(spec["price"]),
                    "price_currency": "USD",
                    "overview": spec["overview"],
                    "duration_days": sum(n for _, n in spec["route"]) + 1,
                    "group_size_min": 2,
                    "group_size_max": 16,
                    "is_active": True,
                },
            )
            if not created:
                skipped_tours += 1
                self.stdout.write(f"  = exists, skipped: {tour.title}")
                continue

            for order, (city_name, nights) in enumerate(spec["route"], start=1):
                TourStop.objects.create(
                    tour=tour, city=cities[city_name], order=order, nights=nights,
                )
            created_tours += 1
            self.stdout.write(self.style.SUCCESS(
                f"  + created: {tour.title} ({len(spec['route'])} stops)"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Done. {created_tours} tour(s) created, {skipped_tours} already existed."
        ))

    def _ensure_cities(self, uz: Country) -> dict[str, City]:
        cities: dict[str, City] = {}
        for name, overview in CITIES.items():
            city, created = City.objects.get_or_create(
                name=name, country=uz, defaults={"overview": overview},
            )
            cities[name] = city
            if created:
                self.stdout.write(f"  + city created: {name}")
        return cities

    def _category(self, slug: str, cache: dict[str, TourCategory]) -> TourCategory:
        if slug not in cache:
            cache[slug] = (
                TourCategory.objects.filter(slug=slug).first()
                or TourCategory.objects.order_by("order").first()
            )
        return cache[slug]
