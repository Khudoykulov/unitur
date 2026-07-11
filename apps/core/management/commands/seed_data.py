"""
Management command: python manage.py seed_data

Seeds the database with realistic sample data for development:
  - 3 continents, 10 countries, 20 cities, 30 attractions
  - 5 tour categories, 30 tours with days and departures
  - 15 hotels with rooms
  - 5 guide categories, 5 articles
  - 20 reviews (approved)
  - 5 tags
"""

import random
import ssl
import time
import urllib.request
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.destinations.models import Attraction, City, Continent, Country
from apps.guides.models import Article, GuideCategory, Tag
from apps.hotels.models import Hotel, HotelAmenity, HotelRoom
from apps.reviews.models import Review
from apps.tours.models import Tour, TourCategory, TourDay, TourDeparture

User = get_user_model()

# ---------------------------------------------------------------------------
# Sample data pools
# ---------------------------------------------------------------------------

CONTINENTS = [
    ("Europe", "europe"),
    ("Asia", "asia"),
    ("Americas", "americas"),
]

COUNTRIES = [
    # (name, continent_slug, currency, language, timezone)
    ("France", "europe", "EUR", "French", "Europe/Paris"),
    ("Italy", "europe", "EUR", "Italian", "Europe/Rome"),
    ("Japan", "asia", "JPY", "Japanese", "Asia/Tokyo"),
    ("Thailand", "asia", "THB", "Thai", "Asia/Bangkok"),
    ("Uzbekistan", "asia", "UZS", "Uzbek", "Asia/Tashkent"),
    ("USA", "americas", "USD", "English", "America/New_York"),
    ("Peru", "americas", "PEN", "Spanish", "America/Lima"),
    ("Spain", "europe", "EUR", "Spanish", "Europe/Madrid"),
    ("India", "asia", "INR", "Hindi", "Asia/Kolkata"),
    ("Brazil", "americas", "BRL", "Portuguese", "America/Sao_Paulo"),
]

CITIES_BY_COUNTRY = {
    "France": [("Paris", 2.3522, 48.8566), ("Nice", 7.2620, 43.7102)],
    "Italy": [("Rome", 12.4964, 41.9028), ("Venice", 12.3155, 45.4408)],
    "Japan": [("Tokyo", 139.6917, 35.6895), ("Kyoto", 135.7681, 35.0116)],
    "Thailand": [("Bangkok", 100.5018, 13.7563), ("Chiang Mai", 98.9853, 18.7883)],
    "Uzbekistan": [("Tashkent", 69.2401, 41.2995), ("Samarkand", 66.9597, 39.6270)],
    "USA": [("New York", -74.0060, 40.7128), ("Los Angeles", -118.2437, 34.0522)],
    "Peru": [("Lima", -77.0428, -12.0464), ("Cusco", -71.9675, -13.5320)],
    "Spain": [("Madrid", -3.7038, 40.4168), ("Barcelona", 2.1734, 41.3851)],
    "India": [("Delhi", 77.1025, 28.7041), ("Mumbai", 72.8777, 19.0760)],
    "Brazil": [("São Paulo", -46.6333, -23.5505), ("Rio de Janeiro", -43.1729, -22.9068)],
}

TOUR_CATEGORIES = [
    ("Adventure", "compass", "Thrilling outdoor experiences"),
    ("Cultural", "building-arch", "Immersive cultural journeys"),
    ("Beach & Relaxation", "beach", "Sun, sea, and serenity"),
    ("Culinary", "chef-hat", "Taste the world"),
    ("Wildlife & Nature", "trees", "Encounter nature's wonders"),
]

AMENITIES = [
    ("Free WiFi", "wifi"),
    ("Swimming Pool", "swimming"),
    ("Gym", "barbell"),
    ("Restaurant", "utensils"),
    ("Spa", "sparkles"),
    ("Parking", "parking"),
    ("Air Conditioning", "air-conditioning"),
    ("Room Service", "room-service"),
]

GUIDE_CATEGORIES = [
    ("Visa & Travel Tips", "id", "Practical visa and entry guidance"),
    ("Safety & Health", "heart-rate-monitor", "Stay safe on your travels"),
    ("Food & Cuisine", "chef-hat", "Culinary adventures worldwide"),
    ("Budget Travel", "coin", "Travel smart and save money"),
    ("Packing Guides", "luggage", "What to pack for every destination"),
]

REVIEW_TITLES = [
    "Absolutely incredible experience!",
    "Best trip of my life",
    "Highly recommend this tour",
    "Professional and attentive staff",
    "Exceeded all expectations",
    "Worth every penny",
    "Perfect organization",
    "Unforgettable memories",
]

# ── Unsplash photo IDs per model ─────────────────────────────────────────────

COUNTRY_PHOTOS = {
    "france":     "photo-1502602898657-3e91760cbb34",
    "italy":      "photo-1552832230-c0197dd311b5",
    "japan":      "photo-1480796927426-f609979314bd",
    "thailand":   "photo-1528181304800-259b08848526",
    "uzbekistan": "photo-1558618666-fcd25c85cd64",
    "usa":        "photo-1485871981521-5b1fd3805eee",
    "peru":       "photo-1587595431973-160d0d94add1",
    "spain":      "photo-1539037116277-4db20889f2d4",
    "india":      "photo-1524492412937-b28074a5d7da",
    "brazil":     "photo-1483729558449-99ef09a8c325",
}

TOUR_PHOTOS = [
    "photo-1431274172761-fca41d930114",
    "photo-1533105079780-92b9be482077",
    "photo-1528360983277-13d401cdc186",
    "photo-1503917988258-f87a78e3c995",
    "photo-1537996194471-e657df975ab4",
    "photo-1512453979798-5ea266f8880c",
]

HOTEL_PHOTOS = [
    "photo-1566073771259-6a8506099945",
    "photo-1445019980597-93fa8acb246c",
    "photo-1551882547-ff40c63fe5fa",
    "photo-1631049307264-da0ec9d70304",
    "photo-1582719508461-905c673771fd",
]

ARTICLE_PHOTOS = [
    "photo-1540959733332-eab4deabeeaf",
    "photo-1431274172761-fca41d930114",
    "photo-1476224203421-9ac39bcb3327",
    "photo-1488646953014-85cb44e25828",
    "photo-1501555088652-021faa106b9b",
]


REVIEW_BODIES = [
    "The tour was perfectly organized from start to finish. Every detail was taken care of and our guide was knowledgeable and friendly.",
    "I traveled solo and felt completely safe and welcome. The group was amazing and I made friends for life.",
    "The hotels were excellent, the food was incredible, and the sights were breathtaking. I cannot recommend this enough.",
    "Our family had an amazing time. The itinerary was perfectly paced for both adults and children.",
    "From the moment we landed to our departure, everything was smooth and professional. Five stars!",
]


class Command(BaseCommand):
    help = "Seed the database with sample travel data"

    # ── SSL context (ignores cert errors on Windows dev) ──────────────────────
    _ssl = None

    def _ssl_ctx(self):
        if self._ssl is None:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self._ssl = ctx
        return self._ssl

    def _fetch_image(self, photo_id, width=800):
        """Download image from Unsplash CDN. Returns ContentFile or None."""
        url = f"https://images.unsplash.com/{photo_id}?w={width}&q=82&fit=crop"
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 TravelPro/1.0"}
        )
        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx(), timeout=20) as r:
                return ContentFile(r.read())
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"    img skip {photo_id}: {exc}"))
            return None

    def _set_img(self, obj, field, photo_id, filename, width=800):
        """Assign an Unsplash image to an ImageField if not already set."""
        if getattr(obj, field):
            return False
        content = self._fetch_image(photo_id, width)
        if content:
            getattr(obj, field).save(filename, content, save=True)
            time.sleep(0.2)
            return True
        return False

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Starting seed_data..."))

        self._create_superuser()
        continents = self._create_continents()
        countries = self._create_countries(continents)
        cities = self._create_cities(countries)
        amenities = self._create_hotel_amenities()
        hotels = self._create_hotels(cities, amenities)
        categories = self._create_tour_categories()
        tours = self._create_tours(categories, countries, hotels)
        self._create_departures(tours)
        articles = self._create_guide_content(tours)
        self._create_reviews(tours, hotels)
        self._assign_images(countries, tours, hotels, articles)

        self.stdout.write(self.style.SUCCESS("Seed complete!"))

    # -----------------------------------------------------------------------
    def _create_superuser(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@travelpro.com", "admin123")
            self.stdout.write("  Created superuser: admin / admin123")

    def _create_continents(self):
        result = {}
        for i, (name, slug) in enumerate(CONTINENTS):
            obj, created = Continent.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "order": i},
            )
            result[slug] = obj
        self.stdout.write(f"  Continents: {len(result)}")
        return result

    def _create_countries(self, continents):
        result = {}
        for i, (name, cont_slug, currency, language, tz) in enumerate(COUNTRIES):
            slug = slugify(name)
            obj, _ = Country.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "continent": continents.get(cont_slug),
                    "currency": currency,
                    "language": language,
                    "timezone": tz,
                    "overview": f"{name} is a beautiful country with rich culture and history.",
                    "best_time_to_visit": "Spring and Autumn",
                    "is_featured": i < 6,
                    "is_active": True,
                    "order": i,
                },
            )
            result[name] = obj
        self.stdout.write(f"  Countries: {len(result)}")
        return result

    def _create_cities(self, countries):
        all_cities = []
        for country_name, city_list in CITIES_BY_COUNTRY.items():
            country = countries.get(country_name)
            if not country:
                continue
            for i, (city_name, lng, lat) in enumerate(city_list):
                slug = slugify(city_name)
                city, _ = City.objects.get_or_create(
                    slug=slug,
                    country=country,
                    defaults={
                        "name": city_name,
                        "overview": f"Discover the beauty and culture of {city_name}.",
                        "latitude": lat,
                        "longitude": lng,
                        "is_featured": i == 0,
                        "is_active": True,
                        "order": i,
                    },
                )
                # Add a sample attraction
                Attraction.objects.get_or_create(
                    slug=slugify(f"{city_name} old town"),
                    city=city,
                    defaults={
                        "name": f"{city_name} Historic Centre",
                        "category": "culture",
                        "description": f"The historic heart of {city_name}.",
                        "is_featured": True,
                        "is_active": True,
                    },
                )
                all_cities.append(city)
        self.stdout.write(f"  Cities: {len(all_cities)}")
        return all_cities

    def _create_hotel_amenities(self):
        amenities = []
        for name, icon in AMENITIES:
            a, _ = HotelAmenity.objects.get_or_create(name=name, defaults={"icon": icon})
            amenities.append(a)
        return amenities

    def _create_hotels(self, cities, amenities):
        hotels = []
        for i, city in enumerate(cities[:15]):
            slug = slugify(f"{city.name} grand hotel {i}")
            hotel, _ = Hotel.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": f"The Grand {city.name}",
                    "city": city,
                    "category": random.choice(["standard", "boutique", "luxury"]),
                    "stars": random.randint(3, 5),
                    "description": f"A premier hotel in the heart of {city.name}.",
                    "price_from": random.randint(80, 400),
                    "is_featured": i < 4,
                    "is_active": True,
                    "order": i,
                },
            )
            hotel.amenities.set(random.sample(amenities, k=min(4, len(amenities))))

            # Add rooms
            for rtype in ["double", "suite"]:
                HotelRoom.objects.get_or_create(
                    hotel=hotel,
                    room_type=rtype,
                    defaults={
                        "capacity": 2,
                        "price_per_night": hotel.price_from * (Decimal("1.5") if rtype == "suite" else Decimal("1")),
                        "is_available": True,
                    },
                )
            hotels.append(hotel)
        self.stdout.write(f"  Hotels: {len(hotels)}")
        return hotels

    def _create_tour_categories(self):
        cats = []
        for i, (name, icon, desc) in enumerate(TOUR_CATEGORIES):
            slug = slugify(name)
            cat, _ = TourCategory.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "icon": icon, "description": desc, "order": i},
            )
            cats.append(cat)
        return cats

    def _create_tours(self, categories, countries, hotels):
        tours = []
        country_list = list(countries.values())
        hotel_list = list(hotels)
        tour_names = [
            "Classic {country} Discovery",
            "Hidden Gems of {country}",
            "{country} Cultural Immersion",
            "Highlights of {country}",
            "Adventure Through {country}",
            "{country} Food & Wine Journey",
        ]
        for i in range(30):
            country = country_list[i % len(country_list)]
            name_tpl = tour_names[i % len(tour_names)]
            title = name_tpl.format(country=country.name)
            slug = slugify(title) + f"-{i}"
            cat = categories[i % len(categories)]
            price = random.choice([799, 1299, 1799, 2499, 3299])
            days = random.choice([7, 10, 14, 21])
            tour, _ = Tour.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "category": cat,
                    "duration_days": days,
                    "group_size_min": 4,
                    "group_size_max": 18,
                    "difficulty": random.choice(["easy", "medium", "hard"]),
                    "price_per_person": price,
                    "price_currency": "USD",
                    "discount_percent": random.choice([0, 0, 5, 10, 15]),
                    "overview": f"Explore the best of {country.name} on this carefully crafted {days}-day journey.",
                    "includes": "Accommodation\nBreakfast daily\nAirport transfers\nEnglish-speaking guide\nAll entrance fees",
                    "excludes": "International flights\nTravel insurance\nPersonal expenses\nOptional activities",
                    "important_notes": "Moderate walking required. Bring comfortable shoes.",
                    "is_featured": i < 6,
                    "is_active": True,
                    "order": i,
                },
            )
            tour.destinations.set([country])
            tour.hotels.set(random.sample(hotel_list, k=min(2, len(hotel_list))))

            # Days
            for day_num in range(1, min(days + 1, 6)):
                TourDay.objects.get_or_create(
                    tour=tour,
                    day_number=day_num,
                    defaults={
                        "title": f"Day {day_num}: Explore {country.name}",
                        "description": f"Today we visit the highlights of {country.name}. Our expert guide will bring history to life.",
                        "meals_included": random.choice(["breakfast", "breakfast_dinner"]),
                        "accommodation": f"Hotel in {country.name}",
                        "transport": "Private coach",
                    },
                )
            tours.append(tour)
        self.stdout.write(f"  Tours: {len(tours)}")
        return tours

    def _create_departures(self, tours):
        count = 0
        today = date.today()
        for tour in tours[:20]:
            for offset in [30, 60, 90, 120]:
                dep_date = today + timedelta(days=offset)
                TourDeparture.objects.get_or_create(
                    tour=tour,
                    departure_date=dep_date,
                    defaults={
                        "return_date": dep_date + timedelta(days=tour.duration_days),
                        "available_seats": 16,
                        "booked_seats": random.randint(0, 8),
                        "status": "open",
                    },
                )
                count += 1
        self.stdout.write(f"  Departures: {count}")

    def _create_guide_content(self, tours):
        user = User.objects.filter(is_superuser=True).first()
        tags = []
        for tag_name in ["solo-travel", "budget", "luxury", "family", "adventure"]:
            t, _ = Tag.objects.get_or_create(name=tag_name, defaults={"slug": tag_name})
            tags.append(t)

        cats = []
        for i, (name, icon, desc) in enumerate(GUIDE_CATEGORIES):
            cat, _ = GuideCategory.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name, "icon": icon, "description": desc, "order": i},
            )
            cats.append(cat)

        article_data = [
            ("10 Tips for First-Time Travelers to Asia", cats[0], "asia"),
            ("The Ultimate Guide to Budget Travel in Europe", cats[3], "europe"),
            ("Must-Try Street Foods Around the World", cats[2], "food"),
            ("How to Stay Safe While Traveling Alone", cats[1], "safety"),
            ("Essential Packing List for a 2-Week Trip", cats[4], "packing"),
        ]
        for i, (title, cat, _) in enumerate(article_data):
            slug = slugify(title)
            art, _ = Article.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "category": cat,
                    "author": user,
                    "excerpt": f"Everything you need to know about {title.lower()}.",
                    "content": f"<h2>{title}</h2><p>Travel is one of the most enriching experiences life has to offer. Whether you are a seasoned globetrotter or planning your first adventure abroad, this guide will help you make the most of your journey.</p><p>Here are our expert tips to ensure a smooth, enjoyable, and memorable trip.</p>",
                    "reading_time_minutes": random.randint(4, 10),
                    "is_published": True,
                    "is_featured": i == 0,
                    "is_active": True,
                },
            )
            art.tags.set(random.sample(tags, k=2))
        self.stdout.write(f"  Articles: {len(article_data)}")
        return list(Article.objects.filter(slug__in=[slugify(t) for t, *_ in article_data]))

    def _assign_images(self, countries, tours, hotels, articles):
        self.stdout.write("  Downloading images from Unsplash...")
        n = 0

        # Countries
        for slug, photo_id in COUNTRY_PHOTOS.items():
            country = countries.get(slug.title()) or countries.get(slug.upper())
            if not country:
                # try case-insensitive match
                for k, v in countries.items():
                    if k.lower() == slug:
                        country = v
                        break
            if country:
                if self._set_img(country, "cover_image", photo_id, f"{slug}-cover.jpg", 1200):
                    n += 1

        # Featured tours (first 6)
        for i, tour in enumerate(tours[:6]):
            photo_id = TOUR_PHOTOS[i % len(TOUR_PHOTOS)]
            fname = f"tour-{i}-cover.jpg"
            if self._set_img(tour, "cover_image", photo_id, fname, 900):
                n += 1

        # Featured hotels (first 5)
        for i, hotel in enumerate(hotels[:5]):
            photo_id = HOTEL_PHOTOS[i % len(HOTEL_PHOTOS)]
            fname = f"hotel-{i}-cover.jpg"
            if self._set_img(hotel, "cover_image", photo_id, fname, 900):
                n += 1

        # Articles
        for i, article in enumerate(articles):
            photo_id = ARTICLE_PHOTOS[i % len(ARTICLE_PHOTOS)]
            fname = f"article-{i}-cover.jpg"
            if self._set_img(article, "cover_image", photo_id, fname, 900):
                n += 1

        self.stdout.write(f"  Images assigned: {n}")

    def _create_reviews(self, tours, hotels):
        count = 0
        countries = ["USA", "UK", "Australia", "Germany", "France", "Japan", "Canada"]
        for i in range(20):
            tour = tours[i % len(tours)]
            rating = random.choice([4, 4, 5, 5, 5])
            Review.objects.get_or_create(
                guest_name=f"Traveler {i + 1}",
                tour=tour,
                defaults={
                    "review_type": "tour",
                    "guest_country": random.choice(countries),
                    "rating": rating,
                    "title": random.choice(REVIEW_TITLES),
                    "body": random.choice(REVIEW_BODIES),
                    "status": "approved",
                    "is_verified": random.choice([True, False]),
                    "travel_date": date.today() - timedelta(days=random.randint(30, 365)),
                },
            )
            count += 1
        self.stdout.write(f"  Reviews: {count}")
