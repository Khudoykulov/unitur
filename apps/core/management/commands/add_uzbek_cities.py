"""Add the main Uzbek (domestic) cities, fetch a cover image for each, and
machine-translate their text into every site language.

Idempotent / resumable: existing cities are reused, images are only fetched
when missing, and translations only fill empty language fields.

    python manage.py add_uzbek_cities
    python manage.py add_uzbek_cities --no-images
    python manage.py add_uzbek_cities --no-translate
"""

import ssl
import time
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.destinations.models import Country
from apps.destinations.models import City

DOMESTIC_COUNTRY = "Uzbek"

# (name, overview, latitude, longitude)
CITIES = [
    ("Tashkent", "The capital of Uzbekistan — a lively mix of leafy boulevards, bustling bazaars, Soviet-era architecture and gleaming modern districts.", 41.2995, 69.2401),
    ("Samarkand", "One of the oldest cities in Central Asia and a jewel of the Silk Road, famed for the majestic Registan, Gur-e-Amir and Shah-i-Zinda.", 39.6270, 66.9750),
    ("Bukhara", "A living museum of the Silk Road with more than a hundred preserved monuments, ancient madrasas, trading domes and the iconic Po-i-Kalyan complex.", 39.7747, 64.4286),
    ("Khiva", "A walled desert city whose old town, Itchan Kala, is an open-air UNESCO museum of minarets, palaces and madrasas.", 41.3783, 60.3639),
    ("Shakhrisabz", "The birthplace of Amir Timur, dotted with the ruins of his grand Ak-Saray Palace and elegant timurid monuments.", 39.0570, 66.8350),
    ("Termez", "An ancient city on the Afghan border with a deep Buddhist and Islamic past, archaeological sites and riverside landscapes.", 37.2242, 67.2783),
    ("Nukus", "The capital of Karakalpakstan, home to the world-renowned Savitsky Museum and a gateway to the Aral Sea region.", 42.4531, 59.6103),
    ("Fergana", "A green, garden city at the heart of the fertile Fergana Valley, known for its silk, ceramics and warm hospitality.", 40.3864, 71.7864),
    ("Kokand", "A former khanate capital in the Fergana Valley, celebrated for the opulent Khan's Palace and historic mosques.", 40.5286, 70.9425),
    ("Margilan", "The silk capital of Uzbekistan, where traditional atlas and adras fabrics are still woven by hand.", 40.4711, 71.7244),
    ("Andijan", "A historic Fergana Valley city, birthplace of the emperor Babur, founder of the Mughal Empire.", 40.7821, 72.3442),
    ("Namangan", "A major Fergana Valley city known for its gardens, crafts and vibrant local bazaars.", 40.9983, 71.6726),
    ("Navoi", "A modern industrial city and a convenient base for exploring the Kyzylkum desert and nearby Silk Road sites.", 40.0844, 65.3792),
    ("Urgench", "The gateway to Khiva and the Khorezm region, set on the edge of the Kyzylkum desert.", 41.5500, 60.6333),
]

# Verified-working Unsplash photo IDs (already used elsewhere in the project).
PHOTO_POOL = [
    "photo-1558618666-fcd25c85cd64",
    "photo-1503917988258-f87a78e3c995",
    "photo-1512453979798-5ea266f8880c",
    "photo-1528360983277-13d401cdc186",
    "photo-1537996194471-e657df975ab4",
    "photo-1533105079780-92b9be482077",
    "photo-1431274172761-fca41d930114",
    "photo-1476514525535-07fb3b4ae5f1",
    "photo-1464822759023-fed622ff2c3b",
    "photo-1488085061387-422e29b40080",
]


class Command(BaseCommand):
    help = "Add the main Uzbek cities with cover images and translations."

    def add_arguments(self, parser):
        parser.add_argument("--no-images", action="store_true", help="Skip image downloads.")
        parser.add_argument("--no-translate", action="store_true", help="Skip auto-translation.")
        parser.add_argument("--width", type=int, default=1200, help="Cover image width.")

    # ── Unsplash fetch (tolerates cert issues on Windows dev) ──────────────
    _ssl = None

    def _ctx(self):
        if self._ssl is None:
            c = ssl.create_default_context()
            c.check_hostname = False
            c.verify_mode = ssl.CERT_NONE
            self._ssl = c
        return self._ssl

    def _fetch(self, photo_id, width):
        url = f"https://images.unsplash.com/{photo_id}?w={width}&q=82&fit=crop"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TravelPro/1.0"})
        try:
            with urllib.request.urlopen(req, context=self._ctx(), timeout=25) as r:
                data = r.read()
            return data if len(data) > 10_000 else None
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(self.style.WARNING(f"    img {photo_id}: {exc}"))
            return None

    def handle(self, *args, **opts):
        country = Country.objects.filter(name_en__icontains=DOMESTIC_COUNTRY).first()
        if not country:
            raise CommandError("No Uzbekistan country found. Run seed_data first.")

        autofill = None
        if not opts["no_translate"]:
            from apps.dashboard.autotranslate import autofill_translations
            autofill = autofill_translations

        created = updated = imaged = translated = 0
        for i, (name, overview, lat, lng) in enumerate(CITIES):
            city, was_created = City.objects.get_or_create(
                name=name,
                country=country,
                defaults={
                    "slug": slugify(name),
                    "overview": overview,
                    "latitude": lat,
                    "longitude": lng,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
                tag = "created"
            else:
                # Fill missing pieces on existing rows without clobbering edits.
                changed = False
                if not city.overview:
                    city.overview = overview; changed = True
                if city.latitude is None:
                    city.latitude = lat; changed = True
                if city.longitude is None:
                    city.longitude = lng; changed = True
                if changed:
                    city.save(); updated += 1
                tag = "exists"

            # Cover image
            if not opts["no_images"] and not city.cover_image:
                for n in range(len(PHOTO_POOL)):
                    pid = PHOTO_POOL[(i + n) % len(PHOTO_POOL)]
                    data = self._fetch(pid, opts["width"])
                    if data:
                        city.cover_image.save(f"{slugify(name)}-cover.jpg", ContentFile(data), save=True)
                        imaged += 1
                        time.sleep(0.2)
                        break

            # Translations
            if autofill:
                n = autofill(city, source_lang="en", overwrite=False, force=True)
                if n:
                    translated += 1

            self.stdout.write(f"  {name:12} [{tag}] img={'yes' if city.cover_image else 'no'}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone — {created} created, {updated} updated, "
            f"{imaged} images fetched, {translated} translated."
        ))
